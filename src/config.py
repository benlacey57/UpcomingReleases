import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration management using Pydantic Settings for type safety and environment validation."""
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "insecure-default-key-for-testing==")
    google_credentials_json: str = os.getenv("GOOGLE_CREDENTIALS_JSON", "{}")
    calendar_id: str = os.getenv("CALENDAR_ID", "primary")
    timezone: str = os.getenv("TIMEZONE", "UTC")
    
    # Feature Flags
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    enable_calendar_sync: bool = os.getenv("ENABLE_CALENDAR_SYNC", "true").lower() == "true"
    enable_git_commit: bool = os.getenv("ENABLE_GIT_COMMIT", "false").lower() == "true"
    enable_api_fetch: bool = os.getenv("ENABLE_API_FETCH", "true").lower() == "true"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
