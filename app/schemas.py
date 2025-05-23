from pydantic import BaseModel, Field
from typing import List, Optional, Literal  # Added Optional, Literal
from datetime import datetime  # Added datetime


class QuestionResponse(BaseModel):
    questions: List[str]


class CareerScores(BaseModel):
    software_development: float = Field(..., alias="Software Development")
    data_science: float = Field(..., alias="Data Science")
    cybersecurity: float = Field(..., alias="Cybersecurity")
    ux_ui_design: float = Field(..., alias="UX/UI Design")

    class Config:
        validate_by_name = True  # Assuming Pydantic v1 or specific compatibility
        # For Pydantic v2, this would typically be:
        # model_config = {"populate_by_name": True}


class CriteriaCategoryScores(BaseModel):
    software_development: float = Field(..., alias="Software Development")
    data_science: float = Field(..., alias="Data Science")
    cybersecurity: float = Field(..., alias="Cybersecurity")
    ux_ui_design: float = Field(..., alias="UX/UI Design")

    class Config:
        validate_by_name = True  # Assuming Pydantic v1 or specific compatibility
        # For Pydantic v2, this would typically be:
        # model_config = {"populate_by_name": True}


class CriteriaScores(BaseModel):
    creativity_innovation: CriteriaCategoryScores = Field(
        ..., alias="Creativity & Innovation"
    )
    problem_solving_logical: CriteriaCategoryScores = Field(
        ..., alias="Problem-Solving & Logical Thinking"
    )
    collaboration_communication: CriteriaCategoryScores = Field(
        ..., alias="Collaboration & Communication"
    )
    learning_style_adaptability: CriteriaCategoryScores = Field(
        ..., alias="Learning Style & Adaptability"
    )
    alignment_career_values: CriteriaCategoryScores = Field(
        ..., alias="Alignment with Career Values & Interests"
    )

    class Config:
        validate_by_name = True


class RecommendationResponse(BaseModel):
    career_scores: CareerScores
    criteria_scores: CriteriaScores
    assessment: str


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
    recommendation_payload: Optional[RecommendationResponse] = None
    # Optionally, Devy might send specific questions or actions
    # next_questions: Optional[List[str]] = None
