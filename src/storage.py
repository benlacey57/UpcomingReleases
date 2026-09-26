import json
import os
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.decorators import log_execution

logger = logging.getLogger(__name__)

class ReleaseStorage:
    """Manages version-controlled state and rolling-TTL cache files with robust JSON corruption recovery."""

    def __init__(self, state_file: str = "data/state.json", cache_file: str = "data/cache.json", log_file: str = "logs/release_history.log") -> None:
        self.state_file = state_file
        self.cache_file = cache_file
        self.log_file = log_file
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        for path in [self.state_file, self.cache_file, self.log_file]:
            dirname = os.path.dirname(path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

    @staticmethod
    def normalize_key(media_type: str, title: str) -> str:
        """Generates a standardized parent normalized key with prefix (tv: or movie:)."""
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        clean_type = media_type.lower().strip()
        return f"{clean_type}:{slug}"

    @log_execution
    def load_state(self) -> Dict[str, Any]:
        if not os.path.exists(self.state_file):
            return {"releases": {}}
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"State file corrupted or unreadable ({e}). Falling back to default state.")
            return {"releases": {}}

    @log_execution
    def save_state(self, state: Dict[str, Any]) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)

    @log_execution
    def load_cache(self) -> Dict[str, Any]:
        if not os.path.exists(self.cache_file):
            return {"last_updated": "", "cached_releases": {}}
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Cache file corrupted or unreadable ({e}). Falling back to default cache.")
            return {"last_updated": "", "cached_releases": {}}

    @log_execution
    def save_cache(self, cache_data: Dict[str, Any]) -> None:
        cache_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=4)

    @log_execution
    def log_event(self, message: str) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp} UTC] {message}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
      
