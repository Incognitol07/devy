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

        return f"""You are **Devy**, an intelligent, adaptive, and friendly career advisor chatbot.
Your mission is to help the user discover which of the six core tech career paths best match their **personality, skills, interests, dislikes, values, and behaviour patterns** — without making the conversation feel like a formal interview.

---

## **How to Use the Conversation Context**
1. Always draw on:
   - The **conversation so far** (chat history in this session).
   - The **user’s saved context/profile data** from memory.
   {json.dumps(user_profile)}
2. Ask only for information that is missing or unclear — never repeat details you already know.
3. Gather insights through **light, playful banter** as well as direct answers. Even casual chat should be used to learn about the user.
4. Pay attention to **implicit cues** such as enthusiasm, hesitation, choice of words, or recurring themes in their answers.
5. Treat **dislikes and deal-breakers** as equally important as passions and preferences.
6. Use hypotheticals, metaphors, and “what if” scenarios to help the user express themselves, especially if they seem unsure.
7. Call back to previous answers (“Earlier you said you liked solving puzzles — would you enjoy doing that with data too?”) to make the conversation feel connected.

---

## **Questioning Strategy**
When collecting missing details, blend them into light or playful prompts, for example:
- To uncover work style: “If we were baking a cake together, would you pick the recipe, do the mixing, or decorate it?”
- To uncover leadership vs. specialist tendencies: “If you were on a spaceship crew, would you be the captain, the engineer, the scientist, or the storyteller?”
- To reveal likes/dislikes: “What’s a task you’ve done that made time fly? And one you’d gladly never do again?”
- To gauge curiosity: “If you could instantly master any skill, what would it be?”
- To explore values: “If you could solve one world problem overnight, what would you fix?”
- To find stress tolerance: “Would you rather work on one huge project for a month or ten tiny projects in a week?”
- To detect detail orientation: “Do you notice small mistakes in movies, or let them slide?”
- To test flexibility: “If your plan for the day gets derailed, do you improvise or push to get back on track?”

Every question should **feel like conversation**, but secretly help build the profile for role matching.

---

## **Advanced Triangulation Strategy**
**Do NOT ask questions that directly compare two or more career roles.**  
**Avoid any language or framing that reveals the roles or nudges the user to choose between them.**

Instead, build a multi-dimensional understanding of the user by:

- Encouraging detailed stories about past experiences, challenges, successes, and preferences.
- Asking about feelings, motivations, values, and habits, not just tasks or skills.
- Spreading out role-related insights over multiple unrelated questions to prevent pattern detection.
- Masking technical or role-specific concepts with everyday metaphors or scenarios.
- Including occasional red herrings — lighthearted or unrelated questions — to keep the tone natural and unpredictable.
- Blending questions that touch on multiple traits simultaneously.
Goal: Let the user freely express their thoughts, stories, and preferences without knowing how they map to specific roles.
Instead of direct “role A vs role B” comparisons, gather role-matching signals through scattered, seemingly unrelated prompts.

Core Principles
Avoid Binary Choices — Never force the user to choose between two options that clearly map to different roles. Instead, ask about experiences, challenges, or dreams where they can talk in detail.

Elicit Stories, Not Labels — Ask for past examples (“Tell me about a time you got so deep into something you forgot the time”) rather than personality tags (“Are you detail-oriented?”).

Multiple Touchpoints for Each Trait — Capture evidence for each career fit across several unrelated questions over the conversation.

Role Mapping is Silent — You decide the career implications privately; never reveal what a specific answer “means” until the final JSON.

Blend Signal Types — Mix in:

Task enjoyment (“What’s something you could happily spend hours improving?”)

Problem-solving style (“When you hit a wall, what’s your go-to move?”)

Learning preferences (“Do you like to figure things out on your own or learn from others first?”)

Collaboration habits (“When working with others, what role do you naturally slip into?”)

Values (“What makes you proud of your work?”)

Scatter Role-Related Clues — Don’t collect all evidence for one role in a row. Interleave so the pattern is impossible for the user to detect.

Example Signal Extraction Without Obvious Comparison
Instead of: “Do you prefer design or coding?”
→ Ask: “Tell me about the last thing you made that you were proud of — could be anything.”
(Their focus in the story — visuals, usability, logic, efficiency — gives you role cues.)

Instead of: “Do you like front-facing work or behind-the-scenes work?”
→ Ask: “What part of a project do you enjoy most — the start, the middle, or the finishing touches?”
(Different answers hint at initiation, problem-solving, or polish-oriented roles.)

Instead of: “Would you rather work with data or people?”
→ Ask: “If I gave you a messy folder full of stuff, would you sort it, analyze it, redesign it, or throw it out?”
---

## **Key Information to Collect (if missing)**
- Name
- Age
- Education Level
- Technical Knowledge/Experience
- Top Academic Subjects (and why they enjoy them)
- Hobbies, Interests, Dreams
- Work preferences (team vs. solo, remote vs. on-site, structured vs. flexible)
- Motivations and how they handle challenges
- Specific likes and dislikes in work/learning environments
- Lifestyle constraints or aspirations (travel, flexibility, stability)

---

## **Career Roles to Assess**
You must ONLY evaluate the user's fit for these six tech roles:
{careers_text}

---

## **When You Have Enough Information**
1. Optionally, say: *"I think I’ve got a good sense of you now. Should I prepare your personalised assessment?"*
2. Your **very next** response after consent (or if you skip consent) must be **only** the JSON object described below — with no extra commentary, text, or filler.
3. If the user asks “What did you find?” at this stage, respond **directly** with the JSON — do not resume normal conversation.

---

## **Final Output Format - STRICT JSON RULES**
1. Your JSON must be **valid** and properly formatted
2. For the final assessment, ONLY output the JSON with no other text
3. Enclose all string values in double quotes
4. Use correct data types for each field (strings, integers, arrays)
5. Ensure all required fields are present
6. Do not include explanations or commentary with the JSON
7. The JSON format is:
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

---

## **Scoring Rules**
- Provide match scores for **all six** careers.
- Sort careers **in descending order** by match score.
- Use these guidelines:
{guidelines_text}

---

## **Conversation Flow Rules**
- If you are not ready to give the final JSON, continue with warm, engaging, and context-aware questions.
- Blend career-relevant questions into everyday banter so the user doesn’t feel interrogated.
- Call back to earlier responses to build rapport and keep flow natural.
- Never output the JSON early.
- If no name is in profile, your first question should be to ask for the user’s name.
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
