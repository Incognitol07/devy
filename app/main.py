from datetime import datetime, timezone
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc  # Added for ordering chat messages
from starlette.middleware.sessions import SessionMiddleware
import uuid
import json
import logging  # ADDED: For detailed logging
from typing import List, Dict, Any  # Ensure Any is imported if not already

# OpenAI SDK for GitHub AI Inference
import openai  # MODIFIED: Changed from azure.ai.inference

from app import models, schemas, config
from app.database import engine, get_db
from app.models import Base

# --- AI Client Initialization ---
# MODIFIED: Renamed variables for clarity with GitHub AI
github_token = None
github_ai_endpoint = None
github_ai_model_name = None
ai_client = None

if not config.settings.GITHUB_TOKEN:
    print(
        "Critical: GitHub Token (GITHUB_TOKEN) not found in settings. AI features will be disabled."
    )
elif not config.settings.AZURE_AI_ENDPOINT:  # This should be the GitHub AI endpoint
    print(
        "Critical: GitHub AI Endpoint (AZURE_AI_ENDPOINT in .env) not found in settings. AI features will be disabled."
    )
elif (
    not config.settings.AZURE_AI_DEPLOYMENT_NAME
):  # This will be the model name like 'openai/gpt-4o'
    print(
        "Critical: GitHub AI Model Name (AZURE_AI_DEPLOYMENT_NAME in .env) not found in settings. AI features will be disabled."
    )
else:
    github_token = config.settings.GITHUB_TOKEN
    github_ai_endpoint = (
        config.settings.AZURE_AI_ENDPOINT
    )  # e.g., "https://models.github.ai/inference"
    github_ai_model_name = (
        config.settings.AZURE_AI_DEPLOYMENT_NAME
    )  # e.g., "openai/gpt-4o"
    try:
        # MODIFIED: Client initialization for OpenAI SDK
        ai_client = openai.OpenAI(
            base_url=github_ai_endpoint,
            api_key=github_token,
        )
        print(
            f"OpenAI client for GitHub AI initialized successfully. Endpoint: {github_ai_endpoint}, Model: {github_ai_model_name}"
        )
    except Exception as e:
        print(f"Error initializing OpenAI client for GitHub AI: {e}")
        ai_client = None


# Initialize FastAPI app
app = FastAPI(title=config.settings.APP_NAME)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=config.settings.SESSION_SECRET_KEY)

# Mount static files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


# Database initialization
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
async def on_startup():
    create_db_and_tables()
    print(f"{config.settings.APP_NAME} started, database tables checked/created.")


@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request, db: Session = Depends(get_db)):
    # Ensure session_id exists in the session
    session_id = request.session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
        logger.info(f"[/] Created new session ID: {session_id}")
    else:
        logger.info(f"[/] Using existing session ID: {session_id}")

    # Load previous chat messages for this session
    chat_messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.timestamp)
        .all()
    )

    # Check if an assessment exists for this session
    existing_assessment = (
        db.query(models.Assessment)
        .filter(models.Assessment.session_id == session_id)
        .first()
    )

    has_assessment = False
    assessment_data = None

    if existing_assessment:
        logger.info(f"[/] Found existing assessment for session {session_id}")
        has_assessment = True
        assessment_data = existing_assessment.assessment_data
    else:
        logger.info(f"[/] No existing assessment found for session {session_id}")

    # Render template with chat messages and assessment data included
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
):
    session_id = request.session.get("session_id")
    logger.info(
        f"[/chat] Session ID: {session_id}, User message: {user_message[:50]}..."
    )  # ADDED
    if not session_id:
        logger.error("[/chat] Session ID missing.")  # ADDED
        raise HTTPException(
            status_code=400, detail="Session ID missing. Please refresh the page."
        )

    db_session = (
        db.query(models.Session).filter(models.Session.id == session_id).first()
    )
    if not db_session:
        logger.warning(
            f"[/chat] Session {session_id} not found in DB, creating new one."
        )  # ADDED
        db_session = models.Session(id=session_id, context_data={"user_profile": {}})
        db.add(db_session)
        # db.commit() # Commit will happen later
        print(f"Session {session_id} created on POST /chat as it was missing.")

    if db_session.context_data is None or "user_profile" not in db_session.context_data:
        logger.info(
            f"[/chat] Initializing user_profile in context_data for session {session_id}"
        )  # ADDED
        db_session.context_data = {"user_profile": {}}
        # db.commit() # Commit will happen later
        print(
            f"Initialized user_profile in context_data for session {session_id} in POST /chat"
        )

    user_profile = db_session.context_data.get("user_profile", {})
    logger.info(
        f"[/chat] User profile for session {session_id}: {user_profile}"
    )  # ADDED

    db_user_msg = models.ChatMessage(
        session_id=session_id, sender="user", content=user_message
    )
    db.add(db_user_msg)
    db.flush()  # Get ID for db_user_msg before AI call if needed for history exclusion

    devy_response_content = "I'm having a little trouble connecting to my brain right now. Please try again in a moment."
    is_assessment_complete = False
    recommendation_payload = None

    if not ai_client:
        logger.error("[/chat] AI client not initialized.")  # ADDED
        print("AI client not initialized. Returning generic error message.")
    else:
        try:
            system_prompt_content = f"""You are Devy, an intelligent and friendly career advisor chatbot. Your goal is to help users discover which of the 6 core tech career paths aligns best with their personality, skills, interests, and background.

Engage in a natural, empathetic conversation to gather information about the user. Key information to gather includes, but is not limited to:
- Name
- Age
- Education Level
- Technical Knowledge/Experience
- Top Academic Subjects (and enjoyable aspects)
- Hobbies, Interests, Dreams
- Work preferences (team vs. solo, environment, etc.)
- Motivations and how they handle challenges

Keep track of the information provided by the user throughout the conversation.
The user's profile data known so far is: {json.dumps(user_profile)}

You must evaluate the user's fit for THESE SIX TECH ROLES ONLY:

1. Frontend Developer
   Focus: Building the visual and interactive parts of websites or web apps that users directly interact with.

2. Backend Developer
   Focus: Creating and managing the behind-the-scenes systems that handle business logic, databases, and APIs.

3. Mobile Developer
   Focus: Developing applications specifically for mobile devices like smartphones and tablets.

4. Data Scientist
   Focus: Analyzing data to uncover patterns, generate insights, and support decision-making.

5. Machine Learning Engineer
   Focus: Building, training, and deploying machine learning models into production systems.

6. UI/UX Designer
   Focus: Designing user experiences and interfaces that are intuitive, aesthetically pleasing, and user-centered.

When you believe you have a comprehensive understanding of the user and enough information to make a well-rounded assessment:
1. You MAY optionally inform the user that you are now ready to generate their assessment and ask for their consent (e.g., "I think I have enough information now, let me prepare your assessment. Should I go ahead?").
2. After such an optional statement, or if you choose to proceed directly, your VERY NEXT response MUST be ONLY the JSON object detailed below.
3. Do not include any other text, explanations, or conversational filler outside this JSON object when providing the assessment.
4. If the user asks a question (e.g., "What did you find?", "Are you sure?", "Well, what did you learn?") immediately after you've indicated readiness or when you are about to provide the assessment, proceed to output the JSON assessment as your response to that question. Do not re-engage in conversation at this point; deliver the assessment as promised.

The JSON object structure is as follows:
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
    {{
      "career_name": "Frontend Developer",
      "match_score": integer (0-100),
      "reasoning": "string",
      "suggested_next_steps": ["string"]
    }},
    {{
      "career_name": "Backend Developer",
      "match_score": integer (0-100),
      "reasoning": "string",
      "suggested_next_steps": ["string"]
    }},
    {{
      "career_name": "Mobile Developer",
      "match_score": integer (0-100),
      "reasoning": "string",
      "suggested_next_steps": ["string"]
    }},
    {{
      "career_name": "Data Scientist",
      "match_score": integer (0-100),
      "reasoning": "string",
      "suggested_next_steps": ["string"]
    }},
    {{
      "career_name": "Machine Learning Engineer",
      "match_score": integer (0-100),
      "reasoning": "string",
      "suggested_next_steps": ["string"]
    }},
    {{
      "career_name": "UI/UX Designer",
      "match_score": integer (0-100),
      "reasoning": "string",
      "suggested_next_steps": ["string"]
    }}
  ],
  "overall_assessment_notes": "string"
}}

Match score guidelines:
- 90-100: Excellent match - perfect alignment with skills, interests, and personality
- 75-89: Strong match - very good alignment with room for growth
- 60-74: Good match - alignment in key areas with some development needed
- 40-59: Moderate match - some alignment but significant development needed
- 0-39: Low match - limited alignment, would require substantial development

IMPORTANT: You MUST provide match scores for ALL SIX career roles, sorted in descending order by match score.

If you are NOT yet at the stage of providing the final JSON assessment, continue the conversation by asking relevant questions or providing supportive feedback. Do not output any JSON unless it's the final assessment.
Your first question, if no prior conversation and no name in profile, should be to ask for the user's name.
"""
            messages_for_ai = [{"role": "system", "content": system_prompt_content}]
            # ... (chat history loading logic remains the same)
            chat_history = (
                db.query(models.ChatMessage)
                .filter(models.ChatMessage.session_id == session_id)
                .order_by(desc(models.ChatMessage.timestamp))
                .limit(10)
                .all()
            )
            chat_history.reverse()

            for msg in chat_history:
                if msg.id == db_user_msg.id:
                    continue
                if msg.sender == "user":
                    messages_for_ai.append({"role": "user", "content": msg.content})
                elif msg.sender == "devy":
                    try:
                        json.loads(msg.content)
                    except json.JSONDecodeError:
                        messages_for_ai.append(
                            {"role": "assistant", "content": msg.content}
                        )

            messages_for_ai.append({"role": "user", "content": user_message})
            logger.info(
                f"[/chat] Messages for AI: {json.dumps(messages_for_ai, indent=2)[:500]}..."
            )  # ADDED

            ai_response = ai_client.chat.completions.create(
                model=github_ai_model_name,
                messages=messages_for_ai,
            )
            raw_ai_response_content = (
                ai_response.choices[0].message.content
                if ai_response.choices and ai_response.choices[0].message
                else ""
            )
            logger.info(
                f"[/chat] Raw AI response content: {raw_ai_response_content}"
            )  # ADDED

            try:
                parsed_assessment = json.loads(raw_ai_response_content)
                logger.info(
                    f"[/chat] Successfully parsed AI response as JSON: {parsed_assessment}"
                )  # ADDED
                recommendation = schemas.RecommendationResponse.model_validate(
                    parsed_assessment
                )
                logger.info(
                    f"[/chat] Successfully validated JSON against RecommendationResponse schema: {recommendation}"
                )  # ADDED

                devy_response_content = (
                    "Here is your personalized career assessment:"  # MODIFIED
                )
                recommendation_payload = recommendation.model_dump()
                is_assessment_complete = True
                logger.info(
                    f"[/chat] Assessment complete. Payload: {recommendation_payload}"
                )  # ADDED

                user_summary = recommendation.user_summary
                if user_summary.name:
                    logger.info(
                        f"[/chat] Assessment contains user name: {user_summary.name}. Attempting to find/create user."
                    )  # ADDED
                    db_user = (
                        db.query(models.User)
                        .filter(models.User.name == user_summary.name)
                        .first()
                    )
                    if not db_user:
                        logger.info(
                            f"[/chat] User {user_summary.name} not found, creating new user."
                        )  # ADDED
                        db_user = models.User(name=user_summary.name)
                        db.add(db_user)
                    else:
                        logger.info(
                            f"[/chat] Found existing user: {db_user.id} - {db_user.name}"
                        )  # ADDED

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
                    logger.info(
                        f"[/chat] Updated db_user fields for {user_summary.name}"
                    )  # ADDED

                    if db_user.id is None:
                        db.flush()
                        logger.info(
                            f"[/chat] Flushed new user {user_summary.name} to get ID: {db_user.id}"
                        )  # ADDED

                    if db_user.id:
                        db_session.user_id = db_user.id
                        logger.info(
                            f"[/chat] Linked session {session_id} to user_id {db_user.id}"
                        )  # ADDED
                        db_assessment = models.Assessment(
                            session_id=session_id,
                            user_id=db_user.id,
                            assessment_data=recommendation.model_dump(),
                        )
                        db.add(db_assessment)
                        logger.info(
                            f"[/chat] Assessment for user {db_user.id} added to session."
                        )  # ADDED
                    else:
                        logger.error(
                            f"[/chat] Could not save assessment as user ID for {user_summary.name} is missing after flush."
                        )  # ADDED
                else:
                    logger.warning(
                        "[/chat] User name missing in assessment summary, cannot update User or save Assessment."
                    )  # ADDED
            except (
                json.JSONDecodeError,
                ValueError,
            ) as e:  # ValueError includes pydantic.ValidationError
                logger.error(
                    f"[/chat] Failed to parse AI response as JSON or validate schema: {e}. Raw response was: {raw_ai_response_content}"
                )  # MODIFIED
                devy_response_content = (
                    raw_ai_response_content  # Keep sending raw content if not JSON
                )
                is_assessment_complete = False
                recommendation_payload = None

            if db_session.user_id and not user_profile.get("name"):
                linked_user = (
                    db.query(models.User)
                    .filter(models.User.id == db_session.user_id)
                    .first()
                )
                if linked_user and linked_user.name:
                    user_profile["name"] = linked_user.name
                    db_session.context_data["user_profile"] = user_profile
                    from sqlalchemy.orm.attributes import flag_modified

                    flag_modified(db_session, "context_data")
                    logger.info(
                        f"[/chat] Updated session context_data with user name: {linked_user.name}"
                    )  # ADDED

        except openai.APIStatusError as e:
            logger.error(
                f"OpenAI API Status Error: {e.status_code} - {e.message}"
            )  # MODIFIED
            print(f"OpenAI API Status Error: {e.status_code} - {e.message}")
            devy_response_content = f"AI Service Error ({e.status_code}): {e.message if e.message else 'Status error from AI service.'}"
        except openai.APIError as e:
            logger.error(f"OpenAI API Error: {e}")  # MODIFIED
            print(f"OpenAI API Error: {e}")
            devy_response_content = f"AI Service Error: {e.message if hasattr(e, 'message') and e.message else 'An unexpected API error occurred.'}"
        except Exception as e:
            logger.error(
                f"Error during AI interaction or response processing: {e}",
                exc_info=True,
            )  # MODIFIED with exc_info
            print(f"Error during AI interaction or response processing: {e}")

    db_devy_msg = models.ChatMessage(
        session_id=session_id, sender="devy", content=devy_response_content
    )
    db.add(db_devy_msg)

    try:  # ADDED try-except for commit
        db.commit()
        logger.info(
            f"[/chat] Database commit successful for session {session_id}."
        )  # ADDED
    except Exception as e:
        logger.error(
            f"[/chat] Database commit failed for session {session_id}: {e}",
            exc_info=True,
        )  # ADDED
        db.rollback()
        # Potentially re-raise or handle gracefully
        # For now, the function will return the potentially stale/error devy_response_content

    # Refresh objects after commit (if successful)
    # ... (refresh logic remains the same)
    if db.is_active:  # ADDED check before refresh
        db.refresh(db_user_msg)
        db.refresh(db_devy_msg)
        db.refresh(db_session)
        if "db_user" in locals() and db_user and db_user.id:
            db.refresh(db_user)
        if "db_assessment" in locals() and db_assessment and db_assessment.id:
            db.refresh(db_assessment)

    logger.info(
        f"[/chat] Returning ChatOutput: is_assessment_complete={is_assessment_complete}, payload_present={recommendation_payload is not None}"
    )  # ADDED
    return schemas.ChatOutput(
        devy_response=devy_response_content,
        session_id=session_id,
        is_assessment_complete=is_assessment_complete,
        recommendation_payload=recommendation_payload,
    )


@app.post("/new-session")
async def create_new_session(request: Request, db: Session = Depends(get_db)):
    """Create a new session and return its ID."""
    logger.info(f"[/new-session] Creating new session")

    # Create a new session ID
    new_session_id = str(uuid.uuid4())

    # Set it in the user's session
    request.session["session_id"] = new_session_id

    # Create a database entry for the new session
    db_session = models.Session(id=new_session_id, context_data={"user_profile": {}})

    try:
        db.add(db_session)
        db.commit()
        logger.info(
            f"[/new-session] Successfully created new session with ID: {new_session_id}"
        )
        return {"success": True, "session_id": new_session_id}
    except Exception as e:
        logger.error(f"[/new-session] Error creating new session: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to create new session: {str(e)}"
        )
