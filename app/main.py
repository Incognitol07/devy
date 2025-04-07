import json
from typing import List
from fastapi import FastAPI, HTTPException, status
from app.config import settings
from app.schemas import QuestionResponse, RecommendationResponse, RecommendationRequest
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

endpoint = "https://models.inference.ai.azure.com"
model_name = "DeepSeek-V3"
token = settings.GITHUB_TOKEN

client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/questions/", response_model=QuestionResponse)
def get_questions():
    response = client.complete(
    messages=[
        SystemMessage(""" You are an expert career advisor with deep insights into human behavior. You are tasked with generating open-ended, projective questions to assess a person's intrinsic traits and decision-making approaches. Your goal is to create relatable questions for beginners, focusing on everyday experiences and simple scenarios. Avoid technical jargon and instead focus on general personality traits and behavioral tendencies."""),
        UserMessage("""Your task is to generate a structured, numbered list of open-ended, projective questions that reveal a person's intrinsic traits, everyday behaviors, and natural decision-making approaches. The questions must be completely relatable and designed specifically for beginners—such as students or teenagers—so that anyone can answer them easily without feeling overwhelmed.

    The questions should:
    - Focus on everyday experiences and simple scenarios that are familiar to young people.
    - Elicit genuine reflections about how the person thinks, collaborates, learns, and makes decisions.
    - Avoid any reference to specific tech roles or technical jargon; instead, focus on general personality traits and behavioral tendencies.
    - Include a mix of general questions as well as scenario-based or hypothetical questions. For scenario-based questions, introduce a relatable character in an engaging narrative that reflects common real-life situations, and then ask the respondent what they would do if they were in that character’s situation, or what advice they would give.

    These insights will later be used to evaluate the candidate’s potential for various tech career paths based on criteria such as:
    - Creativity & Innovation
    - Problem-Solving & Logical Thinking
    - Collaboration & Communication
    - Learning Style & Adaptability
    - Alignment with Career Values & Interests

    Please provide the questions as a plain Python list of strings (e.g., ["Question 1", "Question 2", ...]) with no markdown formatting, no triple backticks, and no newline characters in the output.
    Generate at least 8 to 10 questions."""),
        ],
        max_tokens=1000,
        model=model_name
    )

    questions_list = json.loads(response.choices[0].message.content)
    return {"questions": questions_list}


@app.post("/recommendation/", response_model=RecommendationResponse)
def get_recommendations(request: List[RecommendationRequest]):
    response = client.complete(
        messages=[
            SystemMessage("You are an advanced career assessment system"),
            UserMessage(f"""
            You are an advanced career assessment system. Your task is to evaluate a candidate's responses to a series of projective, open-ended questions designed to reveal their personality and aptitude for various tech career paths. Based on the candidate's answers, assign an overall percentage score for each of the following tech career paths: Software Development, Data Science, Cybersecurity, and UX/UI Design. In addition, break down the scores according to the following evaluation criteria:

            1. Creativity & Innovation:  
            - Assess how well the candidate demonstrates creative thinking and an interest in innovative solutions.

            2. Problem-Solving & Logical Thinking:  
            - Evaluate how effectively the candidate breaks down challenges and approaches finding solutions.

            3. Collaboration & Communication:  
            - Determine how much the candidate values collaboration and whether their responses indicate an ability to work effectively with others.

            4. Learning Style & Adaptability:  
            - Review the candidate’s preferred learning methods and their adaptability to new technologies.

            5. Alignment with Career Values & Interests:  
            - Analyze how the candidate’s values and personal experiences align with the specific demands of each tech domain.

            For each tech career path, calculate:
            - An overall career score (as a percentage).
            - A breakdown of scores for each of the five assessment criteria, such that the sum of these criterion scores exactly equals the overall career score for that domain.

            Ensure that these scores are derived solely from the candidate’s responses. The criterion breakdown should provide insight into the candidate’s strengths and weaknesses for that particular tech career.

            In addition, provide a detailed textual assessment written in a second-person perspective (e.g., "Your decision to ...") that directly addresses the candidate and explains why these scores were assigned. This explanation should include key insights drawn from the candidate’s responses and how those insights informed the scoring.

            Return only the JSON object exactly as specified below without any markdown formatting, code fences, no triple backticks, no newline characters and additional commentary:

            {{
              "career_scores": {{
                "software_development": <percentage>,
                "data_science": <percentage>,
                "cybersecurity": <percentage>,
                "ux_ui_design": <percentage>
              }},
              "criteria_scores": {{
                "creativity_innovation": {{
                  "software_development": <percentage>,
                  "data_science": <percentage>,
                  "cybersecurity": <percentage>,
                  "ux_ui_design": <percentage>
                }},
                "problem_solving_logical": {{
                  "software_development": <percentage>,
                  "data_science": <percentage>,
                  "cybersecurity": <percentage>,
                  "ux_ui_design": <percentage>
                }},
                "collaboration_communication": {{
                  "software_development": <percentage>,
                  "data_science": <percentage>,
                  "cybersecurity": <percentage>,
                  "ux_ui_design": <percentage>
                }},
                "learning_style_adaptability": {{
                  "software_development": <percentage>,
                  "data_science": <percentage>,
                  "cybersecurity": <percentage>,
                  "ux_ui_design": <percentage>
                }},
                "alignment_career_values": {{
                  "software_development": <percentage>,
                  "data_science": <percentage>,
                  "cybersecurity": <percentage>,
                  "ux_ui_design": <percentage>
                }}
              }},
              "assessment": "<detailed explanation of the scoring rationale in second-person, addressing the candidate directly>"
            }}

            Provide a detailed analysis before assigning the percentages, ensuring that the scoring is based solely on the information provided in the candidate’s answers. Make sure that for each career path, the sum of the criterion scores equals the overall career score.

            Here is the candidate's responses:
            {request}
            """),
        ],
        max_tokens=1000,
        model=model_name
    )

    # Parse the JSON response
    try:
        response_data = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid response from the model.")

    return response_data
