# app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    GITHUB_TOKEN: str
    DATABASE_URL: str = (
        "postgresql://user:password@host:port/database"  # Replace with your actual DB connection string
    )
    APP_NAME: str = "Devy Career Advisor"
    SESSION_SECRET_KEY: str = "your_secret_key_here"  # Replace with a strong secret key
    AZURE_AI_ENDPOINT: str = "https://models.github.ai/inference"
    AZURE_AI_DEPLOYMENT_NAME: str = "openai/gpt-4o" # e.g., gpt-35-turbo, gpt-4

    class Config:
        env_file = ".env"  # For loading environment variables from a .env file


# Instantiate settings
settings = Settings()
