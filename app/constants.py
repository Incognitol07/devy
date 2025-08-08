"""
Constants used throughout the Devy Career Advisor application.

This module defines application-wide constants to ensure consistency
and make configuration changes easier to manage.
"""

from typing import List, Dict, Any

# Supported career paths in the system
CAREER_PATHS: List[str] = [
    "Frontend Developer",
    "Backend Developer",
    "Mobile Developer",
    "Data Scientist",
    "Machine Learning Engineer",
    "UI/UX Designer",
]

# Career path descriptions for UI and prompts
CAREER_DESCRIPTIONS: Dict[str, str] = {
    "Frontend Developer": "Building the visual and interactive parts of websites or web apps that users directly interact with.",
    "Backend Developer": "Creating and managing the behind-the-scenes systems that handle business logic, databases, and APIs.",
    "Mobile Developer": "Developing applications specifically for mobile devices like smartphones and tablets.",
    "Data Scientist": "Analyzing data to uncover patterns, generate insights, and support decision-making.",
    "Machine Learning Engineer": "Building, training, and deploying machine learning models into production systems.",
    "UI/UX Designer": "Designing user experiences and interfaces that are intuitive, aesthetically pleasing, and user-centered.",
}

# Match score ranges and their meanings
MATCH_SCORE_RANGES: Dict[str, Dict[str, Any]] = {
    "excellent": {
        "min": 90,
        "max": 100,
        "description": "Excellent match - perfect alignment with skills, interests, and personality",
    },
    "strong": {
        "min": 75,
        "max": 89,
        "description": "Strong match - very good alignment with room for growth",
    },
    "good": {
        "min": 60,
        "max": 74,
        "description": "Good match - alignment in key areas with some development needed",
    },
    "moderate": {
        "min": 40,
        "max": 59,
        "description": "Moderate match - some alignment but significant development needed",
    },
    "low": {
        "min": 0,
        "max": 39,
        "description": "Low match - limited alignment, would require substantial development",
    },
}

# Message sender types
MESSAGE_SENDERS: Dict[str, str] = {"USER": "user", "AI": "devy"}

# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "MAX_MESSAGE_LENGTH": 5000,
    "MIN_MESSAGE_LENGTH": 1,
    "MAX_CHAT_HISTORY": 10,
    "SESSION_TIMEOUT_HOURS": 24,
    "MAX_SESSION_MESSAGES": 100,
}

# API response messages
API_MESSAGES: Dict[str, str] = {
    "SESSION_MISSING": "Session ID missing. Please refresh the page.",
    "MESSAGE_EMPTY": "Message cannot be empty.",
    "MESSAGE_TOO_LONG": "Message is too long (maximum 5000 characters).",
    "AI_UNAVAILABLE": "I'm having trouble connecting to my AI brain right now. Please try again in a moment.",
    "PROCESSING_ERROR": "I'm experiencing some technical difficulties. Please try again in a moment.",
    "ASSESSMENT_COMPLETE": "Here is your personalized career assessment:",
    "SERVER_ERROR": "An unexpected error occurred. Please try again.",
}

# Database constraints
DB_CONSTRAINTS: Dict[str, int] = {
    "MAX_NAME_LENGTH": 100,
    "MAX_CONTENT_LENGTH": 10000,
    "MAX_EDUCATION_LENGTH": 200,
    "MAX_TECHNICAL_KNOWLEDGE_LENGTH": 1000,
    "MAX_INTERESTS_LENGTH": 1000,
}
