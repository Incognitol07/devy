from pydantic import BaseModel, Field
from typing import List

class QuestionResponse(BaseModel):
    questions: List[str]

class CareerScores(BaseModel):
    software_development: float = Field(..., alias="Software Development")
    data_science: float = Field(..., alias="Data Science")
    cybersecurity: float
    ux_ui_design: float = Field(..., alias="UX/UI Design")

    class Config:
        validate_by_name = True

class CriteriaCategoryScores(BaseModel):
    software_development: float = Field(..., alias="Software Development")
    data_science: float = Field(..., alias="Data Science")
    cybersecurity: float = Field(..., alias="Cybersecurity")
    ux_ui_design: float = Field(..., alias="UX/UI Design")

    class Config:
        validate_by_name = True

class CriteriaScores(BaseModel):
    creativity_innovation: CriteriaCategoryScores = Field(..., alias="Creativity & Innovation")
    problem_solving_logical: CriteriaCategoryScores = Field(..., alias="Problem-Solving & Logical Thinking")
    collaboration_communication: CriteriaCategoryScores = Field(..., alias="Collaboration & Communication")
    learning_style_adaptability: CriteriaCategoryScores = Field(..., alias="Learning Style & Adaptability")
    alignment_career_values: CriteriaCategoryScores = Field(..., alias="Alignment with Career Values & Interests")

    class Config:
        validate_by_name = True

class RecommendationResponse(BaseModel):
    career_scores: CareerScores
    criteria_scores: CriteriaScores
    assessment: str

class RecommendationRequest(BaseModel):
    question: str
    answer: str