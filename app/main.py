"""
Main FastAPI application for the Devy Career Advisor.

This module sets up the FastAPI application, configures middleware,
defines API routes, and handles the web interface for the AI-powered
career recommendation system.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app import schemas, config
from app.database import get_db, create_tables
from app.services.chat_service import ChatService, ChatServiceError
from app.services.ai_service import AIServiceError
from app.utils.logging import setup_logging, get_logger
from app.utils.validation import validate_user_message, validate_session_id

# Setup application-wide logging
setup_logging(level="INFO")
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=config.settings.APP_NAME,
    description="AI-powered career advisor for tech professionals",
    version="1.0.0",
)

# Add session middleware for user session management
app.add_middleware(SessionMiddleware, secret_key=config.settings.SESSION_SECRET_KEY)

# Mount static files for CSS, JavaScript, and assets
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

# Setup Jinja2 templates for HTML rendering
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup_event() -> None:
    """
    Application startup event handler.

    Performs initialization tasks including database table creation
    and service validation. Logs startup information for monitoring.
    """
    try:
        create_tables()
        logger.info(f"{config.settings.APP_NAME} started successfully")
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


def get_or_create_session_id(request: Request) -> str:
    """
    Get existing session ID or create a new one.

    Args:
        request: FastAPI request object containing session data.

    Returns:
        str: Session ID for the current user.
    """
    session_id = request.session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
        logger.info(f"Created new session ID: {session_id}")
    return session_id


@app.get("/", response_class=HTMLResponse)
async def get_chat_page(
    request: Request, db: Session = Depends(get_db)
) -> HTMLResponse:
    """
    Serve the main chat interface page.

    Loads the conversation history and any existing assessment for
    the current session, then renders the chat interface with this
    context for a seamless user experience.

    Args:
        request: FastAPI request object.
        db: Database session dependency.

    Returns:
        HTMLResponse: Rendered chat interface page.
    """
    session_id = get_or_create_session_id(request)
    chat_service = ChatService(db)

    # Load conversation history
    chat_messages = chat_service.get_session_messages(session_id)

    # Check for existing assessment
    existing_assessment = chat_service.get_existing_assessment(session_id)
    has_assessment = existing_assessment is not None
    assessment_data = (
        existing_assessment.assessment_data if existing_assessment else None
    )

    logger.info(
        f"Serving chat page for session {session_id} "
        f"(messages: {len(chat_messages)}, "
        f"has_assessment: {has_assessment})"
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "session_id": session_id,
            "app_name": config.settings.APP_NAME,
            "initial_devy_timestamp": datetime.now(timezone.utc).strftime(
                "%H:%M %p UTC"
            ),
            "chat_messages": chat_messages,
            "has_assessment": has_assessment,
            "assessment_data": json.dumps(assessment_data) if assessment_data else None,
        },
    )


@app.post("/chat", response_model=schemas.ChatOutput)
async def handle_chat_message(
    request: Request, user_message: str = Form(...), db: Session = Depends(get_db)
) -> schemas.ChatOutput:
    """
    Process a chat message from the user.

    Handles the complete conversation flow including AI interaction,
    assessment generation, and data persistence. Returns the AI's
    response along with any completed assessment data.

    Args:
        request: FastAPI request object.
        user_message: User's input message from the form.
        db: Database session dependency.

    Returns:
        schemas.ChatOutput: AI response with metadata and assessment data.

    Raises:
        HTTPException: If session is invalid or processing fails.
    """
    # Get session ID from request
    session_id = request.session.get("session_id")
    if not session_id:
        logger.error("Chat request missing session ID")
        raise HTTPException(
            status_code=400, detail="Session ID missing. Please refresh the page."
        )

    # Validate session ID format
    if not validate_session_id(session_id):
        logger.error(f"Invalid session ID format: {session_id}")
        raise HTTPException(
            status_code=400, detail="Invalid session format. Please refresh the page."
        )

    # Validate user message
    is_valid, error_message = validate_user_message(user_message)
    if not is_valid:
        logger.warning(f"Invalid user message: {error_message}")
        raise HTTPException(status_code=400, detail=error_message)

    logger.info(f"Processing chat message for session {session_id}")

    try:
        chat_service = ChatService(db)
        result = await chat_service.process_message(session_id, user_message)

        logger.info(
            f"Chat message processed successfully for session {session_id} "
            f"(assessment_complete: {result.is_assessment_complete})"
        )

        return result

    except (ChatServiceError, AIServiceError) as e:
        logger.error(f"Service error processing chat message: {e}")
        # Return a user-friendly error message
        return schemas.ChatOutput(
            devy_response="I'm experiencing some technical difficulties. Please try again in a moment.",
            session_id=session_id,
            is_assessment_complete=False,
            recommendation_payload=None,
        )

    except Exception as e:
        logger.error(f"Unexpected error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred. Please try again."
        )


@app.post("/new-session")
async def create_new_session(
    request: Request, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new chat session.

    Generates a new session ID and creates the corresponding database
    records. Updates the user's session cookie with the new ID.

    Args:
        request: FastAPI request object.
        db: Database session dependency.

    Returns:
        Dict[str, Any]: Success status and new session ID.

    Raises:
        HTTPException: If session creation fails.
    """
    logger.info("Creating new session")

    try:
        chat_service = ChatService(db)
        new_session_id = chat_service.create_new_session()

        # Update user's session cookie
        request.session["session_id"] = new_session_id

        logger.info(f"New session created successfully: {new_session_id}")
        return {"success": True, "session_id": new_session_id}

    except ChatServiceError as e:
        logger.error(f"Failed to create new session: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create new session: {str(e)}"
        )


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        Dict[str, str]: Application health status.
    """
    return {"status": "healthy", "service": "devy-career-advisor"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
