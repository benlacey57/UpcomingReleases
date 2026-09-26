import os
from dataclasses import dataclass

@dataclass
class Settings:
    """Configuration management using standard Python dataclasses and environment variables."""
    encryption_key: str = os.getenv("ENCRYPTION_KEY", "insecure-default-key-for-testing==")
    google_credentials_json: str = os.getenv("GOOGLE_CREDENTIALS_JSON", "{}")
    calendar_id: str = os.getenv("CALENDAR_ID", "primary")
    
    # Feature Flags
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() == "true"
    enable_calendar_sync: bool = os.getenv("ENABLE_CALENDAR_SYNC", "true").lower() == "true"
    enable_git_commit: bool = os.getenv("ENABLE_GIT_COMMIT", "false").lower() == "true"
    enable_api_fetch: bool = os.getenv("ENABLE_API_FETCH", "true").lower() == "true"

# Simple .env loader fallback if python-dotenv isn't used
def _load_env_file() -> None:
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("'\""))

_load_env_file()
settings = Settings()
