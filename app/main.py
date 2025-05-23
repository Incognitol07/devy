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
from typing import List, Dict, Any

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

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=config.settings.SESSION_SECRET_KEY)

# Mount static files
app.mount(
    "/static",
    StaticFiles(
        directory="c:\\Users\\femia\\Desktop\\Code\\Projects\\devspace\\static"  # Corrected path
    ),
    name="static",
)

# Setup Jinja2 templates
templates = Jinja2Templates(
    directory="c:\\Users\\femia\\Desktop\\Code\\Projects\\devspace\\app\\templates"  # Corrected path
)


# Database initialization
def create_db_and_tables():
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
async def on_startup():
    create_db_and_tables()
    print(f"{config.settings.APP_NAME} started, database tables checked/created.")


@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request, db: Session = Depends(get_db)):
    session_id = request.session.get("session_id")

    if not session_id:
        session_id = str(uuid.uuid4())
        request.session["session_id"] = session_id
        new_session_record = models.Session(
            id=session_id,
            context_data={"user_profile": {}},  # Initialize with empty user profile
        )
        db.add(new_session_record)
        db.commit()
        db.refresh(new_session_record)
        print(f"New session created in DB: {session_id}")
    else:
        db_session = (
            db.query(models.Session).filter(models.Session.id == session_id).first()
        )
        if not db_session:
            new_session_record = models.Session(
                id=session_id, context_data={"user_profile": {}}
            )
            db.add(new_session_record)
            db.commit()
            db.refresh(new_session_record)
            print(f"Re-initialized session in DB from cookie: {session_id}")
        elif (
            db_session.context_data is None
            or "user_profile" not in db_session.context_data
        ):
            db_session.context_data = {"user_profile": {}}
            db.commit()
            db.refresh(db_session)
            print(f"Initialized context_data for existing session {session_id}")
        else:
            print(
                f"Existing session {session_id} confirmed in DB, context_keys: {list(db_session.context_data.keys())}"
            )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "session_id": session_id,
            "app_name": config.settings.APP_NAME,
            # Pass current UTC time for the initial Devy message in template
            "initial_devy_timestamp": datetime.now(timezone.utc).strftime(
                "%H:%M %p UTC"
            ),
        },
    )


@app.post("/chat", response_model=schemas.ChatOutput)
async def handle_chat_message(
    request: Request, user_message: str = Form(...), db: Session = Depends(get_db)
):
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=400, detail="Session ID missing. Please refresh the page."
        )

    db_session = (
        db.query(models.Session).filter(models.Session.id == session_id).first()
    )
    if not db_session:
        db_session = models.Session(id=session_id, context_data={"user_profile": {}})
        db.add(db_session)
        # db.commit() # Commit will happen later
        print(f"Session {session_id} created on POST /chat as it was missing.")

    if db_session.context_data is None or "user_profile" not in db_session.context_data:
        db_session.context_data = {"user_profile": {}}
        # db.commit() # Commit will happen later
        print(
            f"Initialized user_profile in context_data for session {session_id} in POST /chat"
        )

    user_profile = db_session.context_data.get("user_profile", {})

    db_user_msg = models.ChatMessage(
        session_id=session_id, sender="user", content=user_message
    )
    db.add(db_user_msg)
    db.flush()  # Get ID for db_user_msg before AI call if needed for history exclusion

    devy_response_content = "I'm having a little trouble connecting to my brain right now. Please try again in a moment."
    is_assessment_complete = False
    recommendation_payload = None

    if not ai_client:
        print("AI client not initialized. Returning generic error message.")
    else:
        try:
            system_prompt_content = f"""You are Devy, an intelligent and friendly career advisor chatbot. Your goal is to help users discover tech career paths that align with their personality, skills, interests, and background.
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

When you believe you have a comprehensive understanding of the user and enough information to make a well-rounded assessment, you MUST respond ONLY with a JSON object matching the following structure. Do not include any other text or explanations outside this JSON object if you are providing the assessment:
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
      "career_name": "string",
      "match_score": "integer",
      "reasoning": "string",
      "suggested_next_steps": ["string"]
    }}
  ],
  "overall_assessment_notes": "string"
}}

If you are not providing the final JSON assessment, continue the conversation by asking relevant questions or providing supportive feedback. Do not output any JSON unless it's the final assessment.
Your first question, if no prior conversation and no name in profile, should be to ask for the user's name.
"""

            # MODIFIED: Message format for OpenAI SDK
            messages_for_ai = [{"role": "system", "content": system_prompt_content}]

            chat_history = (
                db.query(models.ChatMessage)
                .filter(models.ChatMessage.session_id == session_id)
                .order_by(desc(models.ChatMessage.timestamp))
                .limit(10)
                .all()
            )
            chat_history.reverse()

            for msg in chat_history:
                if (
                    msg.id == db_user_msg.id
                ):  # Exclude the current user message we just added
                    continue
                if msg.sender == "user":
                    messages_for_ai.append(
                        {"role": "user", "content": msg.content}
                    )  # MODIFIED
                elif msg.sender == "devy":
                    try:
                        # Avoid re-feeding a previous JSON assessment as an assistant message
                        json.loads(msg.content)
                        # If it's JSON, assume it might be an old assessment and skip it.
                        # A more robust way would be to flag assessment messages in DB.
                    except json.JSONDecodeError:
                        messages_for_ai.append(
                            {"role": "assistant", "content": msg.content}
                        )  # MODIFIED

            # Add the current user's message
            messages_for_ai.append(
                {"role": "user", "content": user_message}
            )  # MODIFIED

            # MODIFIED: API call for OpenAI SDK
            ai_response = ai_client.chat.completions.create(
                model=github_ai_model_name,  # Use the model name from config
                messages=messages_for_ai,
                # temperature=1.0, # Optional parameters
                # top_p=1.0,
                # max_tokens=1000
            )
            raw_ai_response_content = (
                ai_response.choices[0].message.content
                if ai_response.choices and ai_response.choices[0].message
                else ""
            )

            # Process AI Response (logic remains largely the same)
            try:
                parsed_assessment = json.loads(raw_ai_response_content)
                recommendation = schemas.RecommendationResponse.model_validate(
                    parsed_assessment
                )
                devy_response_content = f"Thank you! I've completed your career profile assessment. Here are the results:"
                recommendation_payload = recommendation.model_dump()
                is_assessment_complete = True

                user_summary = recommendation.user_summary
                if user_summary.name:
                    db_user = (
                        db.query(models.User)
                        .filter(models.User.name == user_summary.name)
                        .first()
                    )
                    if not db_user:
                        db_user = models.User(name=user_summary.name)
                        db.add(db_user)
                        # db.flush() # Will be flushed with commit

                    # Update user fields
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

                    if (
                        db_user.id is None
                    ):  # If new user, flush to get ID before creating assessment
                        db.flush()

                    if db_user.id:
                        db_session.user_id = db_user.id
                        db_assessment = models.Assessment(
                            session_id=session_id,
                            user_id=db_user.id,
                            assessment_data=recommendation.model_dump(),
                        )
                        db.add(db_assessment)
                    else:
                        print(
                            f"Could not save assessment as user ID for {user_summary.name} is missing after flush."
                        )
                else:
                    print(
                        "User name missing in assessment summary, cannot update User or save Assessment."
                    )
            except (json.JSONDecodeError, ValueError) as e:
                devy_response_content = raw_ai_response_content
                is_assessment_complete = False
                recommendation_payload = None

            # Update user_profile in session context if AI provided new info (this is complex)
            # For now, user_profile is mainly passed to AI. AI uses history.
            # The definitive update to user_profile in context_data could happen if AI explicitly states updates,
            # or we parse it from conversation. Simpler: rely on final assessment's user_summary.
            # If name was learned and user created/linked:
            if db_session.user_id and not user_profile.get("name"):
                linked_user = (
                    db.query(models.User)
                    .filter(models.User.id == db_session.user_id)
                    .first()
                )
                if (
                    linked_user and linked_user.name
                ):  # Ensure linked_user and name exist
                    user_profile["name"] = linked_user.name
                    db_session.context_data["user_profile"] = user_profile
                    # Flag context_data as modified for SQLAlchemy
                    from sqlalchemy.orm.attributes import flag_modified

                    flag_modified(db_session, "context_data")

        # MODIFIED: Specific error handling for OpenAI SDK
        except openai.APIStatusError as e:
            print(f"OpenAI API Status Error: {e.status_code} - {e.message}")
            devy_response_content = f"AI Service Error ({e.status_code}): {e.message if e.message else 'Status error from AI service.'}"
        except openai.APIError as e:
            print(f"OpenAI API Error: {e}")
            devy_response_content = f"AI Service Error: {e.message if hasattr(e, 'message') and e.message else 'An unexpected API error occurred.'}"
        except Exception as e:
            print(f"Error during AI interaction or response processing: {e}")
            # devy_response_content is already set to a fallback (or overridden by more specific AI errors)

    db_devy_msg = models.ChatMessage(
        session_id=session_id, sender="devy", content=devy_response_content
    )
    db.add(db_devy_msg)

    db.commit()
    # Refresh objects after commit
    db.refresh(db_user_msg)
    db.refresh(db_devy_msg)
    db.refresh(db_session)
    if (
        "db_user" in locals() and db_user and db_user.id
    ):  # Check if db_user was defined and has an id
        db.refresh(db_user)
    if (
        "db_assessment" in locals() and db_assessment and db_assessment.id
    ):  # Check if db_assessment was defined and has an id
        db.refresh(db_assessment)

    return schemas.ChatOutput(
        devy_response=devy_response_content,
        session_id=session_id,
        is_assessment_complete=is_assessment_complete,
        recommendation_payload=recommendation_payload,
    )
