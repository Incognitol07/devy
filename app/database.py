"""
Database configuration and session management for Devy Career Advisor.

This module provides database connection setup, session management,
and utility functions for SQLAlchemy ORM operations.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings


# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    # Connection pool settings for production use
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,  # Recycle connections every hour
)

# Session factory for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for getting database sessions in FastAPI routes.

    Creates a new database session for each request and ensures proper
    cleanup after the request is completed. Use this as a dependency
    in FastAPI route functions.

    Yields:
        Session: SQLAlchemy database session.

    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    Create all database tables defined in the models.

    This function should be called during application startup
    to ensure all necessary tables exist in the database.
    """
    from app.models import Base

    Base.metadata.create_all(bind=engine)
