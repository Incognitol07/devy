"""
Logging utility module for consistent application logging.

Provides standardized logging configuration and helper functions
for consistent log formatting throughout the application.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    include_timestamp: bool = True,
) -> None:
    """
    Set up application-wide logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_string: Custom log format string (uses default if None).
        include_timestamp: Whether to include timestamps in log messages.
    """
    if format_string is None:
        if include_timestamp:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        else:
            format_string = "%(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override any existing configuration
    )

    # Set specific loggers to appropriate levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__ of the calling module).

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)


def log_function_call(func_name: str, **kwargs) -> None:
    """
    Log a function call with its parameters.

    Useful for debugging and tracing application flow.

    Args:
        func_name: Name of the function being called.
        **kwargs: Function parameters to log.
    """
    logger = get_logger("function_tracer")
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"Calling {func_name}({params})")


def log_performance(func_name: str, duration: float) -> None:
    """
    Log performance metrics for a function.

    Args:
        func_name: Name of the function that was timed.
        duration: Execution duration in seconds.
    """
    logger = get_logger("performance")
    logger.info(f"{func_name} completed in {duration:.3f}s")
