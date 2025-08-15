import logging
import sys
from typing import Optional
from .settings import settings


def setup_logging() -> logging.Logger:
    """Setup application logging with configuration from settings."""

    # Create logger
    logger = logging.getLogger("hacker_news_app")
    logger.setLevel(getattr(logging, settings.log_level))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for the application."""
    if name:
        return logging.getLogger(f"hacker_news_app.{name}")
    return logging.getLogger("hacker_news_app")


# Create default logger
logger = get_logger()
