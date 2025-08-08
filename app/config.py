"""
Configuration module for the Devy Career Advisor application.

This module manages all application settings, environment variables,
and configuration parameters. Uses Pydantic Settings for validation
and type safety.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with validation and environment variable support.

    All settings can be overridden via environment variables or a .env file.
    Required settings will raise validation errors if not provided.

    Attributes:
        GITHUB_TOKEN: Authentication token for GitHub AI API access.
        DATABASE_URL: PostgreSQL connection string for data persistence.
        APP_NAME: Display name for the application.
        SESSION_SECRET_KEY: Secret key for session encryption and security.
        AZURE_AI_ENDPOINT: GitHub AI inference endpoint URL.
        AZURE_AI_DEPLOYMENT_NAME: Model name to use for AI requests.
    """

    # Required configuration
    GITHUB_TOKEN: str

    # Database configuration
    DATABASE_URL: str = "postgresql://user:password@host:port/database"

    # Application settings
    APP_NAME: str = "Devy Career Advisor"
    SESSION_SECRET_KEY: str = "your_secret_key_here"

    # AI service configuration
    AZURE_AI_ENDPOINT: str = "https://models.github.ai/inference"
    AZURE_AI_DEPLOYMENT_NAME: str = "openai/gpt-4o"

    class Config:
        """Pydantic configuration for settings management."""

        env_file = ".env"  # Load environment variables from .env file
        case_sensitive = True  # Environment variables are case-sensitive


# Global settings instance
settings = Settings()
