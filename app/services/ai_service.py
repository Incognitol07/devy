"""
AI Service module for handling interactions with GitHub AI models.

This module provides a clean interface for AI communication, including
client initialization, conversation management, and response processing.
"""

import json
from typing import Dict, List, Optional, Any

import openai
from pydantic import ValidationError

from app.config import settings
from app.schemas import RecommendationResponse
from app.constants import CAREER_PATHS, CAREER_DESCRIPTIONS, MATCH_SCORE_RANGES
from app.utils.logging import get_logger
from app.utils.validation import sanitize_string

logger = get_logger(__name__)


class AIServiceError(Exception):
    """Custom exception for AI service related errors."""

    pass


class AIService:
    """
    Service class for managing AI interactions and conversation processing.

    Handles GitHub AI client initialization, message formatting, and response
    parsing for the career recommendation system.
    """

    def __init__(self):
        """Initialize the AI service with GitHub AI configuration."""
        self.client: Optional[openai.OpenAI] = None
        self.model_name: Optional[str] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Initialize the OpenAI client for GitHub AI integration.

        Raises:
            AIServiceError: If required configuration is missing or client
                          initialization fails.
        """
        # Validate required configuration
        if not settings.GITHUB_TOKEN:
            raise AIServiceError("GitHub Token (GITHUB_TOKEN) not found in settings")

        if not settings.AZURE_AI_ENDPOINT:
            raise AIServiceError(
                "GitHub AI Endpoint (AZURE_AI_ENDPOINT) not found in settings"
            )

        if not settings.AZURE_AI_DEPLOYMENT_NAME:
            raise AIServiceError(
                "GitHub AI Model Name (AZURE_AI_DEPLOYMENT_NAME) not found in settings"
            )

        try:
            self.client = openai.OpenAI(
                base_url=settings.AZURE_AI_ENDPOINT,
                api_key=settings.GITHUB_TOKEN,
            )
            self.model_name = settings.AZURE_AI_DEPLOYMENT_NAME

            logger.info(
                f"AI client initialized successfully. "
                f"Endpoint: {settings.AZURE_AI_ENDPOINT}, "
                f"Model: {self.model_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            raise AIServiceError(f"Client initialization failed: {e}")

    def is_available(self) -> bool:
        """
        Check if the AI service is available for use.

        Returns:
            bool: True if client is initialized and ready, False otherwise.
        """
        return self.client is not None and self.model_name is not None

    def _build_system_prompt(self, user_profile: Dict[str, Any]) -> str:
        """
        Build the system prompt for the AI conversation.

        Args:
            user_profile: Dictionary containing user's profile information
                        collected throughout the conversation.

        Returns:
            str: Formatted system prompt for the AI model.
        """
        # Build career paths section dynamically from constants
        career_sections = []
        for i, career in enumerate(CAREER_PATHS, 1):
            description = CAREER_DESCRIPTIONS.get(career, "No description available.")
            career_sections.append(f"{i}. {career}\n   Focus: {description}")

        careers_text = "\n\n".join(career_sections)

        # Build match score guidelines from constants
        score_guidelines = []
        for range_name, range_info in MATCH_SCORE_RANGES.items():
            score_guidelines.append(
                f"- {range_info['min']}-{range_info['max']}: {range_info['description']}"
            )

        guidelines_text = "\n".join(score_guidelines)

        # Build career recommendations JSON template
        json_recommendations = []
        for career in CAREER_PATHS:
            json_recommendations.append(
                f"""    {{
      "career_name": "{career}",
      "match_score": integer (0-100),
      "reasoning": "string",
      "suggested_next_steps": ["string"]
    }}"""
            )

        json_template = ",\n".join(json_recommendations)

        return f"""You are Devy, an intelligent and friendly career advisor chatbot. Your goal is to help users discover which of the 6 core tech career paths aligns best with their personality, skills, interests, and background.

Engage in a natural, empathetic conversation to gather information about the user. Key information to gather includes, but is not limited to:
- Name
- Age
- Education Level
- Technical Knowledge/Experience
- Top Academic Subjects (and enjoyable aspects)
- Hobbies, Interests, Dreams
- Work preferences (team vs. solo, environment, etc.)
- Motivations and how they handle challenges

Keep track of the information provided by the user throughout the conversation.
The user's profile data known so far is: {json.dumps(user_profile)}

You must evaluate the user's fit for THESE SIX TECH ROLES ONLY:

{careers_text}

When you believe you have a comprehensive understanding of the user and enough information to make a well-rounded assessment:
1. You MAY optionally inform the user that you are now ready to generate their assessment and ask for their consent (e.g., "I think I have enough information now, let me prepare your assessment. Should I go ahead?").
2. After such an optional statement, or if you choose to proceed directly, your VERY NEXT response MUST be ONLY the JSON object detailed below.
3. Do not include any other text, explanations, or conversational filler outside this JSON object when providing the assessment.
4. If the user asks a question (e.g., "What did you find?", "Are you sure?", "Well, what did you learn?") immediately after you've indicated readiness or when you are about to provide the assessment, proceed to output the JSON assessment as your response to that question. Do not re-engage in conversation at this point; deliver the assessment as promised.

The JSON object structure is as follows:
{{
  "user_summary": {{
    "name": "string",
    "age": "string | null",
    "education_level": "string | null",
    "technical_knowledge": "string | null",
    "top_subjects": ["string"],
    "subject_aspects": "string | null",
    "interests_dreams": "string | null",
    "other_notes": "string | null"
  }},
  "career_recommendations": [
{json_template}
  ],
  "overall_assessment_notes": "string"
}}

Match score guidelines:
{guidelines_text}

IMPORTANT: You MUST provide match scores for ALL SIX career roles, sorted in descending order by match score.

If you are NOT yet at the stage of providing the final JSON assessment, continue the conversation by asking relevant questions or providing supportive feedback. Do not output any JSON unless it's the final assessment.
Your first question, if no prior conversation and no name in profile, should be to ask for the user's name.
"""

    def _format_conversation_history(
        self, chat_history: List[Any], current_message_id: int
    ) -> List[Dict[str, str]]:
        """
        Format chat history for AI consumption.

        Args:
            chat_history: List of ChatMessage objects from database.
            current_message_id: ID of the current message to exclude from history.

        Returns:
            List[Dict[str, str]]: Formatted messages for AI model.
        """
        messages = []

        for msg in chat_history:
            # Skip the current message to avoid duplication
            if msg.id == current_message_id:
                continue

            # Add user messages as-is
            if msg.sender == "user":
                messages.append({"role": "user", "content": msg.content})
            # Only add assistant messages that aren't JSON assessments
            elif msg.sender == "devy":
                try:
                    # Skip messages that are JSON assessments
                    json.loads(msg.content)
                except json.JSONDecodeError:
                    # This is a regular conversation message
                    messages.append({"role": "assistant", "content": msg.content})

        return messages

    async def process_conversation(
        self,
        user_message: str,
        user_profile: Dict[str, Any],
        chat_history: List[Any],
        current_message_id: int,
    ) -> tuple[str, bool, Optional[RecommendationResponse]]:
        """
        Process a conversation turn with the AI model.

        Args:
            user_message: The user's input message.
            user_profile: Current user profile data.
            chat_history: Previous conversation messages.
            current_message_id: ID of current message to exclude from history.

        Returns:
            tuple: (response_content, is_assessment_complete, recommendation_payload)

        Raises:
            AIServiceError: If AI service is not available or request fails.
        """
        if not self.is_available():
            raise AIServiceError("AI service is not available")

        try:
            # Build conversation messages for AI
            messages = [
                {"role": "system", "content": self._build_system_prompt(user_profile)}
            ]

            # Add conversation history
            history_messages = self._format_conversation_history(
                chat_history, current_message_id
            )
            messages.extend(history_messages)

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            logger.info(f"Sending {len(messages)} messages to AI model")

            # Make AI request
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )

            # Extract response content
            if not response.choices or not response.choices[0].message:
                raise AIServiceError("Empty response from AI model")

            response_content = response.choices[0].message.content
            logger.info("Received response from AI model")

            # Try to parse as assessment JSON
            try:
                parsed_assessment = json.loads(response_content)
                # Validate against schema
                recommendation = RecommendationResponse.model_validate(
                    parsed_assessment
                )

                logger.info("Successfully parsed AI response as assessment")
                return (
                    "Here is your personalized career assessment:",
                    True,
                    recommendation,
                )

            except (json.JSONDecodeError, ValidationError) as e:
                # This is a regular conversation message, not an assessment
                logger.debug(f"Response is not a valid assessment: {e}")
                return response_content, False, None

        except openai.APIStatusError as e:
            logger.error(f"OpenAI API Status Error: {e.status_code} - {e.message}")
            error_msg = f"AI Service Error ({e.status_code}): {e.message or 'Status error from AI service.'}"
            return error_msg, False, None

        except openai.APIError as e:
            logger.error(f"OpenAI API Error: {e}")
            error_msg = f"AI Service Error: {getattr(e, 'message', 'An unexpected API error occurred.')}"
            return error_msg, False, None

        except Exception as e:
            logger.error(f"Unexpected error during AI interaction: {e}", exc_info=True)
            return (
                "I'm having trouble processing your request. Please try again in a moment.",
                False,
                None,
            )


# Global AI service instance
ai_service = AIService()
