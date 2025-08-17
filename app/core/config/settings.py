from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str = "sqlite:///./data/hacker_news.db"

    # Redis Configuration
    redis_url: str = "redis://redis:6379/0"

    # Hacker News API Configuration
    hacker_news_api_base_url: str = "https://hacker-news.firebaseio.com/v0"

    # Application Configuration
    fetch_interval_minutes: int = 30
    cache_ttl_seconds: int = 300
    max_concurrent_requests: int = 10

    # Celery Configuration
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    # Logging
    log_level: str = "INFO"
    log_file_path: str = "./logs/app.log"
    log_rotation: str = "daily"  # daily, size, or none
    log_max_size_mb: int = 100  # Maximum file size in MB for size rotation
    log_backup_count: int = 30  # Number of backup files to keep


    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# Create global settings instance
settings = Settings()
