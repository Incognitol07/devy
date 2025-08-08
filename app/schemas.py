"""
Pydantic schemas for the Devy Career Advisor application.

This module defines the data validation and serialization schemas used
for API requests and responses. All schemas follow Pydantic v2 conventions
and provide comprehensive validation for the career assessment system.
"""

from datetime import datetime
from typing import List, Optional, Literal, Dict, Any

from pydantic import BaseModel, Field


class UserSummary(BaseModel):
    """
    Schema for user profile summary extracted from conversation.

    Contains the essential information about a user gathered during
    the chat interaction, as determined by the AI assessment process.

    Attributes:
        name: User's name (required for creating user records).
        age: User's age as string (AI may provide non-numeric values).
        education_level: Current education status or highest degree.
        technical_knowledge: Description of technical background and experience.
        top_subjects: List of favorite academic subjects.
        subject_aspects: What the user enjoys about their favorite subjects.
        interests_dreams: User's hobbies, interests, and career aspirations.
        other_notes: Additional relevant information from the conversation.
    """

    name: str
    age: Optional[str] = None
    education_level: Optional[str] = None
    technical_knowledge: Optional[str] = None
    top_subjects: Optional[List[str]] = Field(default_factory=list)
    subject_aspects: Optional[str] = None
    interests_dreams: Optional[str] = None
    other_notes: Optional[str] = None


class CareerRecommendationItem(BaseModel):
    """
    Schema for individual career recommendation with scoring and guidance.

    Represents a single career path evaluation including match score,
    reasoning for the assessment, and actionable next steps for the user.

    Attributes:
        career_name: Name of the tech career path being evaluated.
        match_score: Compatibility score from 0-100 based on user profile.
        reasoning: AI's explanation for why this career fits (or doesn't fit).
        suggested_next_steps: List of actionable steps to pursue this career.
    """

    career_name: str
    match_score: int = Field(ge=0, le=100, description="Score from 0-100")
    reasoning: str
    suggested_next_steps: List[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    """
    Complete career assessment response schema.

    Contains the full assessment results including user summary,
    individual career recommendations, and overall analysis. This is
    the primary output format from the AI assessment process.

    Attributes:
        user_summary: Extracted user profile information.
        career_recommendations: List of all six career evaluations.
        overall_assessment_notes: General insights and recommendations.
    """

    user_summary: UserSummary
    career_recommendations: List[CareerRecommendationItem]
    overall_assessment_notes: str


class UserProfile(BaseModel):
    """
    Schema for user profile information collected during onboarding.

    Represents structured user information as it's being collected
    during the conversation, before the final assessment is generated.

    Attributes:
        name: User's name.
        age: User's age in years.
        education_level: Current education status.
        favorite_subjects: List of preferred academic subjects.
        dreams_goals: User's aspirations and career goals.
    """

    name: str
    age: Optional[int] = None
    education_level: Optional[str] = None
    favorite_subjects: Optional[List[str]] = None
    dreams_goals: Optional[str] = None


class Message(BaseModel):
    """
    Schema for individual chat messages.

    Represents a single message in the conversation history,
    used for internal processing and API responses.

    Attributes:
        sender: Who sent the message ("user" or "devy").
        content: The message text content.
        timestamp: When the message was created.
    """

    sender: Literal["user", "devy"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatInput(BaseModel):
    """
    Schema for incoming chat message requests.

    Validates user input for chat interactions, ensuring
    proper message format and session identification.

    Attributes:
        user_message: The user's input text.
        session_id: Optional session identifier for context.
    """

    user_message: str
    session_id: Optional[str] = None


class ChatOutput(BaseModel):
    """
    Schema for chat response from the AI system.

    Contains the AI's response along with metadata about the
    conversation state and any completed assessments.

    Attributes:
        devy_response: The AI's text response to the user.
        session_id: Session identifier for maintaining context.
        is_assessment_complete: Whether a career assessment was completed.
        recommendation_payload: Complete assessment data if available.
    """

    devy_response: str
    session_id: str
    is_assessment_complete: bool = False
    recommendation_payload: Optional[RecommendationResponse] = None


# Legacy schemas - kept for backward compatibility but marked as deprecated
class QuestionResponse(BaseModel):
    """
    Legacy schema for question-based interactions.

    @deprecated This schema is maintained for backward compatibility
    but is not used in the current conversation-based system.
    """

    questions: List[str]


class RecommendationRequest(BaseModel):
    """
    Legacy schema for question-answer based recommendations.

    @deprecated This schema is maintained for backward compatibility
    but is not used in the current conversation-based system.
    """

    question: str
    answer: str
