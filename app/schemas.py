from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any  # Added Dict, Any
from datetime import datetime


class QuestionResponse(BaseModel):
    questions: List[str]


# class CareerScores(BaseModel): # This model is not used in the new AI JSON structure
#     software_development: float = Field(..., alias="Software Development")
#     data_science: float = Field(..., alias="Data Science")
#     cybersecurity: float = Field(..., alias="Cybersecurity")
#     ux_ui_design: float = Field(..., alias="UX/UI Design")
#
#     class Config:
#         validate_by_name = True
#         # model_config = {"populate_by_name": True} # Pydantic v2
#
# class CriteriaCategoryScores(BaseModel): # Not used
#     software_development: float = Field(..., alias="Software Development")
#     data_science: float = Field(..., alias="Data Science")
#     cybersecurity: float = Field(..., alias="Cybersecurity")
#     ux_ui_design: float = Field(..., alias="UX/UI Design")
#
#     class Config:
#         validate_by_name = True
#         # model_config = {"populate_by_name": True} # Pydantic v2
#
# class CriteriaScores(BaseModel): # Not used
#     creativity_innovation: CriteriaCategoryScores = Field(
#         ..., alias="Creativity & Innovation"
#     )
#     problem_solving_logical: CriteriaCategoryScores = Field(
#         ..., alias="Problem-Solving & Logical Thinking"
#     )
#     collaboration_communication: CriteriaCategoryScores = Field(
#         ..., alias="Collaboration & Communication"
#     )
#     learning_style_adaptability: CriteriaCategoryScores = Field(
#         ..., alias="Learning Style & Adaptability"
#     )
#     alignment_career_values: CriteriaCategoryScores = Field(
#         ..., alias="Alignment with Career Values & Interests"
#     )
#
#     class Config:
#         validate_by_name = True
#
# # The old RecommendationResponse is being replaced
# class RecommendationResponse(BaseModel):
#     career_scores: CareerScores
#     criteria_scores: CriteriaScores
#     assessment: str


# --- NEW Pydantic models for AI Assessment JSON ---
class UserSummary(BaseModel):
    name: str
    age: Optional[str] = None  # AI might send as string or null
    education_level: Optional[str] = None
    technical_knowledge: Optional[str] = None
    top_subjects: Optional[List[str]] = Field(default_factory=list)
    subject_aspects: Optional[str] = None
    interests_dreams: Optional[str] = None
    other_notes: Optional[str] = None


class CareerRecommendationItem(BaseModel):
    career_name: str
    match_score: int  # Assuming integer, e.g., 95 for 95%
    reasoning: str
    suggested_next_steps: List[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):  # RENAMED and RESTRUCTURED
    user_summary: UserSummary
    career_recommendations: List[CareerRecommendationItem]
    overall_assessment_notes: str


# --- END NEW Pydantic models for AI Assessment JSON ---


class RecommendationRequest(BaseModel):
    question: str
    answer: str


# New Models for Chat-based Interaction and Data Storage


class UserProfile(BaseModel):
    """Stores user's profile information collected during onboarding."""

    name: str
    age: Optional[int] = None
    education_level: Optional[str] = None
    favorite_subjects: Optional[List[str]] = None
    dreams_goals: Optional[str] = None


class Message(BaseModel):
    """Represents a single message in the chat history (for DB storage or internal use)."""

    sender: Literal["user", "devy"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatInput(BaseModel):
    """Represents the input from the user in a chat turn."""

    user_message: str
    session_id: Optional[str] = None  # To maintain context across requests


class ChatOutput(BaseModel):
    """Represents Devy's response in a chat turn."""

    devy_response: str
    session_id: str  # To be stored by the client and sent back
    is_assessment_complete: bool = False
    # If assessment is complete, the final recommendation is sent
    # MODIFIED: Ensure this uses the new RecommendationResponse model
    recommendation_payload: Optional[RecommendationResponse] = None
    # Optionally, Devy might send specific questions or actions
    # next_questions: Optional[List[str]] = None
