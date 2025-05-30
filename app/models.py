from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid  # For generating session IDs

# Placeholder for Database URL - will be moved to config.py
DATABASE_URL = "postgresql://user:password@host:port/database"  # Replace with your actual DB connection string

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True)  # Allow null name initially

    age = Column(Integer, nullable=True)
    education_level = Column(String, nullable=True)
    technical_knowledge = Column(String, nullable=True)
    top_subjects = Column(JSON, nullable=True)  # List of strings
    subject_aspects = Column(String, nullable=True)
    interests_dreams = Column(String, nullable=True)

    sessions = relationship("Session", back_populates="user")
    assessments = relationship("Assessment", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(
        String, primary_key=True, default=generate_uuid, index=True
    )  # Using UUID for session_id
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # User can be anonymous initially
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # To store context like scores being accumulated, etc.
    context_data = Column(JSON, default=lambda: {"user_profile": {}})

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
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    sender = Column(String, nullable=False)  # "user" or "devy"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    # To store any inferred traits or insights from this message
    inferred_insights = Column(JSON, nullable=True)

    session = relationship("Session", back_populates="messages")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), unique=True, nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # Added ForeignKey to User

    # Consolidated field to store the full AI-generated assessment JSON
    assessment_data = Column(JSON, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("Session", back_populates="assessment")
    user = relationship(
        "User", back_populates="assessments"
    )  # Added relationship back to User


# Engine and session setup (can be moved to a database.py file)
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base.metadata.create_all(bind=engine) # To create tables; typically called once in main.py
