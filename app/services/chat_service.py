"""
Chat Service module for managing conversation flow and session handling.

This module provides functionality for managing chat sessions, processing
user messages, and coordinating between AI responses and database operations.
"""

import uuid
from typing import Dict, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import desc

from app import models, schemas
from app.services.ai_service import ai_service, AIServiceError
from app.utils.logging import get_logger
from app.utils.validation import sanitize_string, validate_assessment_data

logger = get_logger(__name__)


class ChatServiceError(Exception):
    """Custom exception for chat service related errors."""

    pass


class ChatService:
    """
    Service class for managing chat conversations and session state.

    Handles session creation, message processing, user profile management,
    and coordination between AI responses and database persistence.
    """

    def __init__(self, db: Session):
        """
        Initialize the chat service with a database session.

        Args:
            db: SQLAlchemy database session for persistence operations.
        """
        self.db = db

    def ensure_session_exists(self, session_id: str) -> models.Session:
        """
        Ensure a session exists in the database, creating it if necessary.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            models.Session: The database session object.
        """
        db_session = (
            self.db.query(models.Session)
            .filter(models.Session.id == session_id)
            .first()
        )

        if not db_session:
            logger.info(f"Creating new session: {session_id}")
            db_session = models.Session(
                id=session_id, context_data={"user_profile": {}}
            )
            self.db.add(db_session)
            # Note: commit happens in the calling function

        # Ensure context_data structure exists
        if (
            db_session.context_data is None
            or "user_profile" not in db_session.context_data
        ):
            logger.info(f"Initializing user_profile for session: {session_id}")
            db_session.context_data = {"user_profile": {}}

        return db_session

    def get_chat_history(
        self, session_id: str, limit: int = 10
    ) -> list[models.ChatMessage]:
        """
        Retrieve recent chat history for a session.

        Args:
            session_id: Session identifier to get history for.
            limit: Maximum number of messages to retrieve.

        Returns:
            list[models.ChatMessage]: List of chat messages in chronological order.
        """
        messages = (
            self.db.query(models.ChatMessage)
            .filter(models.ChatMessage.session_id == session_id)
            .order_by(desc(models.ChatMessage.timestamp))
            .limit(limit)
            .all()
        )

        # Return in chronological order (oldest first)
        return list(reversed(messages))

    def save_user_message(self, session_id: str, content: str) -> models.ChatMessage:
        """
        Save a user message to the database.

        Args:
            session_id: Session identifier.
            content: Message content from the user.

        Returns:
            models.ChatMessage: The saved message object.
        """
        # Sanitize user input before saving
        sanitized_content = sanitize_string(content)

        message = models.ChatMessage(
            session_id=session_id, sender="user", content=sanitized_content
        )
        self.db.add(message)
        self.db.flush()  # Get ID before processing
        return message

    def save_ai_message(self, session_id: str, content: str) -> models.ChatMessage:
        """
        Save an AI response message to the database.

        Args:
            session_id: Session identifier.
            content: AI response content.

        Returns:
            models.ChatMessage: The saved message object.
        """
        message = models.ChatMessage(
            session_id=session_id, sender="devy", content=content
        )
        self.db.add(message)
        return message

    def _update_user_from_assessment(
        self, recommendation: schemas.RecommendationResponse, session: models.Session
    ) -> Optional[models.User]:
        """
        Update or create user from assessment data.

        Args:
            recommendation: Validated recommendation response from AI.
            session: Database session object to link user to.

        Returns:
            Optional[models.User]: The updated/created user object, or None if
                                 no name provided in assessment.
        """
        user_summary = recommendation.user_summary

        if not user_summary.name:
            logger.warning("No user name in assessment, cannot create/update user")
            return None

        # Find or create user
        db_user = (
            self.db.query(models.User)
            .filter(models.User.name == user_summary.name)
            .first()
        )

        if not db_user:
            logger.info(f"Creating new user: {user_summary.name}")
            db_user = models.User(name=user_summary.name)
            self.db.add(db_user)
        else:
            logger.info(f"Updating existing user: {user_summary.name}")

        # Update user fields from assessment
        db_user.age = (
            int(user_summary.age)
            if user_summary.age and user_summary.age.isdigit()
            else None
        )
        db_user.education_level = user_summary.education_level
        db_user.technical_knowledge = user_summary.technical_knowledge
        db_user.top_subjects = user_summary.top_subjects
        db_user.subject_aspects = user_summary.subject_aspects
        db_user.interests_dreams = user_summary.interests_dreams

        # Flush to get user ID
        if db_user.id is None:
            self.db.flush()

        # Link session to user
        if db_user.id:
            session.user_id = db_user.id
            logger.info(f"Linked session {session.id} to user {db_user.id}")

        return db_user

    def _save_assessment(
        self,
        session_id: str,
        user_id: int,
        recommendation: schemas.RecommendationResponse,
    ) -> models.Assessment:
        """
        Save assessment results to the database.

        Args:
            session_id: Session identifier.
            user_id: User ID to link assessment to.
            recommendation: Validated recommendation data.

        Returns:
            models.Assessment: The saved assessment object.
        """
        # Validate assessment data before saving
        assessment_data = recommendation.model_dump()
        is_valid, errors = validate_assessment_data(assessment_data)

        if not is_valid:
            logger.warning(f"Assessment validation failed: {errors}")
            # Still save it but log the issues

        assessment = models.Assessment(
            session_id=session_id, user_id=user_id, assessment_data=assessment_data
        )
        self.db.add(assessment)
        logger.info(f"Saved assessment for user {user_id}")
        return assessment

    def _update_session_profile(
        self, session: models.Session, user: models.User
    ) -> None:
        """
        Update session's user profile context with user data.

        Args:
            session: Database session object.
            user: User object with profile information.
        """
        if user and user.name:
            user_profile = session.context_data.get("user_profile", {})
            if not user_profile.get("name"):
                user_profile["name"] = user.name
                session.context_data["user_profile"] = user_profile
                # Mark the field as modified for SQLAlchemy
                flag_modified(session, "context_data")
                logger.info(f"Updated session context with user name: {user.name}")

    async def process_message(
        self, session_id: str, user_message: str
    ) -> schemas.ChatOutput:
        """
        Process a user message and generate an appropriate response.

        This method orchestrates the entire conversation flow:
        1. Ensures session exists
        2. Saves user message
        3. Gets AI response
        4. Handles assessment completion if applicable
        5. Saves AI response
        6. Commits changes

        Args:
            session_id: Session identifier.
            user_message: User's input message.

        Returns:
            schemas.ChatOutput: Complete response with AI message and metadata.

        Raises:
            ChatServiceError: If processing fails at any stage.
        """
        try:
            # Ensure session exists and get user profile
            db_session = self.ensure_session_exists(session_id)
            user_profile = db_session.context_data.get("user_profile", {})

            # Save user message
            user_msg = self.save_user_message(session_id, user_message)

            # Get recent chat history for context
            chat_history = self.get_chat_history(session_id)

            # Process with AI service
            if not ai_service.is_available():
                response_content = (
                    "I'm having trouble connecting to my AI brain right now. "
                    "Please try again in a moment."
                )
                is_assessment_complete = False
                recommendation_payload = None
            else:
                try:
                    response_content, is_assessment_complete, recommendation_payload = (
                        await ai_service.process_conversation(
                            user_message, user_profile, chat_history, user_msg.id
                        )
                    )
                except AIServiceError as e:
                    logger.error(f"AI service error: {e}")
                    response_content = str(e)
                    is_assessment_complete = False
                    recommendation_payload = None

            # Handle assessment completion
            if is_assessment_complete and recommendation_payload:
                # Update/create user from assessment data
                db_user = self._update_user_from_assessment(
                    recommendation_payload, db_session
                )

                # Save assessment if user was created/updated
                if db_user and db_user.id:
                    self._save_assessment(
                        session_id, db_user.id, recommendation_payload
                    )

                    # Update session context with user name
                    self._update_session_profile(db_session, db_user)

            # Save AI response
            ai_msg = self.save_ai_message(session_id, response_content)

            # Commit all changes
            self.db.commit()
            logger.info(f"Successfully processed message for session {session_id}")

            # Refresh objects after commit
            if self.db.is_active:
                self.db.refresh(user_msg)
                self.db.refresh(ai_msg)
                self.db.refresh(db_session)

            return schemas.ChatOutput(
                devy_response=response_content,
                session_id=session_id,
                is_assessment_complete=is_assessment_complete,
                recommendation_payload=recommendation_payload,
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            self.db.rollback()
            raise ChatServiceError(f"Failed to process message: {e}")

    def create_new_session(self) -> str:
        """
        Create a new chat session with a unique ID.

        Returns:
            str: New session ID.

        Raises:
            ChatServiceError: If session creation fails.
        """
        try:
            new_session_id = str(uuid.uuid4())

            db_session = models.Session(
                id=new_session_id, context_data={"user_profile": {}}
            )

            self.db.add(db_session)
            self.db.commit()

            logger.info(f"Created new session: {new_session_id}")
            return new_session_id

        except Exception as e:
            logger.error(f"Error creating new session: {e}", exc_info=True)
            self.db.rollback()
            raise ChatServiceError(f"Failed to create new session: {e}")

    def get_session_messages(self, session_id: str) -> list[models.ChatMessage]:
        """
        Get all chat messages for a session.

        Args:
            session_id: Session identifier.

        Returns:
            list[models.ChatMessage]: All messages for the session in chronological order.
        """
        return (
            self.db.query(models.ChatMessage)
            .filter(models.ChatMessage.session_id == session_id)
            .order_by(models.ChatMessage.timestamp)
            .all()
        )

    def get_existing_assessment(self, session_id: str) -> Optional[models.Assessment]:
        """
        Get existing assessment for a session if one exists.

        Args:
            session_id: Session identifier.

        Returns:
            Optional[models.Assessment]: Assessment object if found, None otherwise.
        """
        return (
            self.db.query(models.Assessment)
            .filter(models.Assessment.session_id == session_id)
            .first()
        )
