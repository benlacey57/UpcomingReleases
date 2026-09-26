import json
import os
import re
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from src.decorators import log_execution

logger = logging.getLogger(__name__)

class ReleaseStorage:
    """Manages version-controlled state, rolling-TTL cache, media registry, and audit logs with normalized keys."""

    def __init__(
        self,
        state_file: str = "data/state.json",
        cache_file: str = "data/cache.json",
        log_file: str = "logs/release_history.log",
        registry_file: str = "data/media_registry.json",
        tracked_file: str = "data/tracked_media.json"
    ) -> None:
        self.state_file = state_file
        self.cache_file = cache_file
        self.log_file = log_file
        self.registry_file = registry_file
        self.tracked_file = tracked_file
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensures that parent directories for all managed files exist."""
        for path in [self.state_file, self.cache_file, self.log_file, self.registry_file, self.tracked_file]:
            dirname = os.path.dirname(path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)

    @staticmethod
    def normalize_key(media_type: str, title: str, season: Optional[int] = None, episode: Optional[int] = None) -> str:
        """Generates a standardized normalized key with prefix (tv: or movie:)."""
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        clean_type = media_type.lower().strip()
        if clean_type == "tv" and season is not None and episode is not None:
            return f"tv:{slug}-s{season:02d}e{episode:02d}"
        return f"{clean_type}:{slug}"

    @log_execution
    def load_state(self) -> Dict[str, Any]:
        """Loads execution state file."""
        if not os.path.exists(self.state_file):
            return {"processed_releases": []}
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    @log_execution
    def save_state(self, state: Dict[str, Any]) -> None:
        """Saves execution state file."""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)

    @log_execution
    def load_cache(self) -> Dict[str, Any]:
        """Loads rolling-TTL cache file."""
        if not os.path.exists(self.cache_file):
            return {"last_updated": "", "cached_releases": {}}
        with open(self.cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    @log_execution
    def save_cache(self, cache_data: Dict[str, Any]) -> None:
        """Saves rolling-TTL cache file with timestamp."""
        cache_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=4)

    @log_execution
    def load_tracked_media(self) -> List[Dict[str, Any]]:
        """Loads locally tracked media items from manifest file."""
        if not os.path.exists(self.tracked_file):
            return []
        with open(self.tracked_file, "r", encoding="utf-8") as f:
            return json.load(f).get("items", [])

    @log_execution
    def save_tracked_media(self, items: List[Dict[str, Any]]) -> None:
        """Saves locally tracked media items to manifest file."""
        with open(self.tracked_file, "w", encoding="utf-8") as f:
            json.dump({"items": items}, f, indent=4)

    @log_execution
    def add_tracked_media(self, item: Dict[str, Any]) -> None:
        """Adds a new movie or TV series item to track."""
        items = self.load_tracked_media()
        items.append(item)
        self.save_tracked_media(items)

    @log_execution
    def load_media_registry(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads master canonical media objects (studios, tv, movies) from registry file."""
        if not os.path.exists(self.registry_file):
            return {"studios": [], "tv_series": [], "movies": []}
        with open(self.registry_file, "r", encoding="utf-8") as f:
            return json.load(f)

    @log_execution
    def save_media_registry(self, registry: Dict[str, List[Dict[str, Any]]]) -> None:
        """Saves master canonical media objects to registry file."""
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=4)

    @log_execution
    def log_event(self, message: str) -> None:
        """Appends a structured timestamped entry to the version-controlled log file."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp} UTC] {message}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
