import logging
import logging.handlers
import sys
import os
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

    # Add file handler if log_file_path is configured
    if hasattr(settings, 'log_file_path') and settings.log_file_path:
        # Ensure log directory exists
        log_dir = os.path.dirname(settings.log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Create appropriate file handler based on rotation settings
        rotation_type = getattr(settings, 'log_rotation', 'none')
        
        # Type annotation for file handler
        file_handler: logging.Handler
        
        if rotation_type == 'daily':
            # Daily rotation: creates files like app.log.2024-01-01
            file_handler = logging.handlers.TimedRotatingFileHandler(
                settings.log_file_path,
                when='midnight',
                interval=1,
                backupCount=getattr(settings, 'log_backup_count', 30),
                encoding='utf-8'
            )
            file_handler.suffix = "%Y-%m-%d"
        elif rotation_type == 'size':
            # Size-based rotation: creates files like app.log.1, app.log.2, etc.
            max_size = getattr(settings, 'log_max_size_mb', 100) * 1024 * 1024  # Convert MB to bytes
            file_handler = logging.handlers.RotatingFileHandler(
                settings.log_file_path,
                maxBytes=max_size,
                backupCount=getattr(settings, 'log_backup_count', 30),
                encoding='utf-8'
            )
        else:
            # No rotation: simple file handler
            file_handler = logging.FileHandler(settings.log_file_path, encoding='utf-8')
        
        file_handler.setLevel(getattr(logging, settings.log_level))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Configure SQLAlchemy logging to file only (echo=True handles console output)
        sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
        sqlalchemy_logger.setLevel(logging.INFO)
        # Only add file handler to avoid duplicate console output
        if not any(isinstance(h, type(file_handler)) for h in sqlalchemy_logger.handlers):
            sqlalchemy_logger.addHandler(file_handler)

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
