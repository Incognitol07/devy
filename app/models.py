"""
Database models for the Devy Career Advisor application.

This module defines the SQLAlchemy ORM models for managing users, sessions,
chat messages, and career assessments. All models follow SQLAlchemy best
practices and include proper relationships and constraints.
"""

from datetime import datetime
import uuid
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def generate_uuid() -> str:
    """
    Generate a unique UUID string for session identifiers.

    Returns:
        str: A new UUID4 string.
    """
    return str(uuid.uuid4())


class User(Base):
    """
    User model representing individuals using the career advisor system.

    Stores personal information collected during the assessment process,
    including demographics, educational background, and interests. Users
    can have multiple sessions and assessments over time.

    Attributes:
        id: Primary key, auto-incrementing integer.
        name: User's name, collected during conversation.
        age: User's age in years (optional).
        education_level: Current education level (e.g., "High School", "Bachelor's").
        technical_knowledge: Description of technical background and experience.
        top_subjects: JSON list of favorite academic subjects.
        subject_aspects: What the user enjoys about their favorite subjects.
        interests_dreams: User's hobbies, interests, and career aspirations.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True)

    # Personal information
    age = Column(Integer, nullable=True)
    education_level = Column(String, nullable=True)
    technical_knowledge = Column(String, nullable=True)

    # Academic and interest information
    top_subjects = Column(JSON, nullable=True)  # List of strings
    subject_aspects = Column(String, nullable=True)
    interests_dreams = Column(String, nullable=True)

    # Relationships
    sessions = relationship("Session", back_populates="user")
    assessments = relationship("Assessment", back_populates="user")


class Session(Base):
    """
    Session model representing individual conversation sessions.

    Each session represents a complete interaction cycle with the career
    advisor, potentially spanning multiple chat messages and culminating
    in a career assessment. Sessions maintain conversation context and
    can be linked to users once identity is established.

    Attributes:
        id: Primary key, UUID string for session identification.
        user_id: Foreign key to User table (nullable for anonymous sessions).
        created_at: Timestamp when session was created.
        updated_at: Timestamp when session was last modified.
        context_data: JSON field storing conversation context and user profile data.
    """

    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Context storage for conversation state and user profile
    context_data = Column(JSON, default=lambda: {"user_profile": {}})

    # Relationships
    user = relationship("User", back_populates="sessions")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )
    assessment = relationship(
        "Assessment",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    """
    Chat message model for storing conversation history.

    Represents individual messages in the conversation between users and
    the AI career advisor. Messages are linked to sessions and include
    metadata for conversation tracking and analysis.

    Attributes:
        id: Primary key, auto-incrementing integer.
        session_id: Foreign key linking to the Session.
        sender: Message sender, either "user" or "devy".
        content: The actual message content/text.
        timestamp: When the message was created.
        inferred_insights: Optional JSON field for storing AI-extracted insights.
    """

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)

    # Message metadata
    sender = Column(String, nullable=False)  # "user" or "devy"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Optional field for storing insights extracted from this message
    inferred_insights = Column(JSON, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="messages")


class Assessment(Base):
    """
    Assessment model for storing completed career evaluations.

    Represents the final career recommendation assessment generated by the AI
    after sufficient conversation with the user. Contains comprehensive
    evaluation results including career matches, scores, and recommendations.

    Attributes:
        id: Primary key, auto-incrementing integer.
        session_id: Foreign key to the Session where assessment was generated.
        user_id: Foreign key to the User who received the assessment.
        assessment_data: JSON field containing the complete assessment results.
        created_at: Timestamp when assessment was completed.
    """

    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Complete assessment results as JSON
    assessment_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="assessment")
    user = relationship("User", back_populates="assessments")
