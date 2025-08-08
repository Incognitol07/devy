"""
Data validation utilities for the Devy Career Advisor.

Provides helper functions for validating and sanitizing user input,
session data, and other application data to ensure data integrity
and security.
"""

import re
from typing import Any, Dict, List, Optional, Union

from app.constants import CAREER_PATHS, DEFAULT_CONFIG


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input string by removing potentially harmful content.

    Args:
        text: Input string to sanitize.
        max_length: Maximum allowed length for the string.

    Returns:
        str: Sanitized string safe for processing and storage.
    """
    if not isinstance(text, str):
        return ""

    # Remove excessive whitespace and limit length
    sanitized = re.sub(r"\s+", " ", text.strip())[:max_length]

    # Remove potential HTML/script tags for basic XSS protection
    sanitized = re.sub(r"<[^>]*>", "", sanitized)

    return sanitized


def validate_session_id(session_id: str) -> bool:
    """
    Validate that a session ID has the correct format.

    Args:
        session_id: Session identifier to validate.

    Returns:
        bool: True if session ID is valid, False otherwise.
    """
    if not isinstance(session_id, str):
        return False

    # Check if it's a valid UUID format
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
    )
    return bool(uuid_pattern.match(session_id))


def validate_user_message(message: str) -> tuple[bool, Optional[str]]:
    """
    Validate user chat message for basic requirements.

    Args:
        message: User's chat message to validate.

    Returns:
        tuple: (is_valid, error_message) - error_message is None if valid.
    """
    if not isinstance(message, str):
        return False, "Message must be a string"

    # Check minimum length
    if len(message.strip()) < DEFAULT_CONFIG["MIN_MESSAGE_LENGTH"]:
        return False, "Message cannot be empty"

    # Check maximum length
    if len(message) > DEFAULT_CONFIG["MAX_MESSAGE_LENGTH"]:
        return (
            False,
            f"Message is too long (maximum {DEFAULT_CONFIG['MAX_MESSAGE_LENGTH']} characters)",
        )

    # Check for potential spam patterns
    if message.count(message[0]) > len(message) * 0.8:
        return False, "Message appears to be spam"

    return True, None


def validate_assessment_data(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate assessment data structure and content.

    Args:
        data: Assessment data dictionary to validate.

    Returns:
        tuple: (is_valid, list_of_errors).
    """
    errors = []

    if not isinstance(data, dict):
        return False, ["Assessment data must be a dictionary"]

    # Check required top-level keys
    required_keys = [
        "user_summary",
        "career_recommendations",
        "overall_assessment_notes",
    ]
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required key: {key}")

    # Validate user_summary
    if "user_summary" in data:
        user_summary = data["user_summary"]
        if not isinstance(user_summary, dict):
            errors.append("user_summary must be a dictionary")
        elif "name" not in user_summary or not user_summary["name"]:
            errors.append("user_summary must contain a non-empty name")

    # Validate career_recommendations
    if "career_recommendations" in data:
        recommendations = data["career_recommendations"]
        if not isinstance(recommendations, list):
            errors.append("career_recommendations must be a list")
        elif len(recommendations) != len(CAREER_PATHS):
            errors.append(
                f"career_recommendations must contain exactly {len(CAREER_PATHS)} items"
            )
        else:
            for i, rec in enumerate(recommendations):
                if not isinstance(rec, dict):
                    errors.append(f"Recommendation {i} must be a dictionary")
                    continue

                # Check required fields in each recommendation
                rec_required = [
                    "career_name",
                    "match_score",
                    "reasoning",
                    "suggested_next_steps",
                ]
                for field in rec_required:
                    if field not in rec:
                        errors.append(f"Recommendation {i} missing field: {field}")

                # Validate match_score
                if "match_score" in rec:
                    score = rec["match_score"]
                    if not isinstance(score, int) or score < 0 or score > 100:
                        errors.append(
                            f"Recommendation {i} match_score must be integer 0-100"
                        )

    return len(errors) == 0, errors


def extract_career_names() -> List[str]:
    """
    Get the list of valid career names for validation.

    Returns:
        List[str]: List of all supported career paths.
    """
    return CAREER_PATHS.copy()


def normalize_career_name(name: str) -> Optional[str]:
    """
    Normalize a career name to match expected format.

    Args:
        name: Career name to normalize.

    Returns:
        Optional[str]: Normalized career name or None if not recognized.
    """
    if not isinstance(name, str):
        return None

    # Create mapping for case-insensitive matching
    valid_careers = extract_career_names()
    name_lower = name.lower().strip()

    for career in valid_careers:
        if career.lower() == name_lower:
            return career

    return None
