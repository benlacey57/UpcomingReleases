import abc
import logging
from typing import List, Dict, Any, Optional
from src.decorators import log_execution, retry_on_failure
from src.storage import ReleaseStorage

logger = logging.getLogger(__name__)

class BaseReleaseChecker(abc.ABC):
    """Abstract Base Class for checking media release updates following SOLID principles."""

    @abc.abstractmethod
    def fetch_releases(self) -> Dict[str, Dict[str, Any]]:
        """Fetches upcoming releases grouped by parent media key."""
        pass

class TMDBReleaseChecker(BaseReleaseChecker):
    """Concrete implementation for fetching specific watchlist release updates with nested episode mapping."""

    def __init__(self, tracked_items: List[Dict[str, Any]], storage: Optional[ReleaseStorage] = None) -> None:
        self.tracked_items = tracked_items
        self.storage = storage or ReleaseStorage()

    @retry_on_failure(retries=3, delay=1.0)
    @log_execution
    def fetch_releases(self) -> Dict[str, Dict[str, Any]]:
        grouped_releases: Dict[str, Dict[str, Any]] = {}
        
        for item in self.tracked_items:
            media_type = item.get("type", "movie")
            title = item.get("title", "Unknown")
            key = ReleaseStorage.normalize_key(media_type, title)
            category = f"{media_type}-releases"
            
            if key not in grouped_releases:
                grouped_releases[key] = {
                    "title": title,
                    "category": category,
                    "type": media_type,
                    "episodes": {} if media_type == "tv" else None
                }
            
            if media_type == "tv":
                season = item.get("season", 1)
                episode = item.get("episode", 1)
                ep_key = f"s{season:02d}e{episode:02d}"
                ep_name = item.get("episode_name", f"Episode {episode}")
                
                grouped_releases[key]["episodes"][ep_key] = {
                    "episode_name": ep_name,
                    "date": item.get("release_date", "2026-12-31"),
                    "synced": False
                }
            else:
                grouped_releases[key]["date"] = item.get("release_date", "2026-12-31")
                grouped_releases[key]["synced"] = False
                
        msg = f"Fetched {len(grouped_releases)} watchlist items."
        logger.info(msg)
        self.storage.log_event(f"WATCHLIST_FETCH: {msg}")
        return grouped_releases


class StudioReleaseChecker(BaseReleaseChecker):
    """Dedicated studio/franchise catalog checker (e.g., Marvel, DC, Disney) handling mixed media types."""

    def __init__(self, studio_name: str, raw_mock_data: Optional[List[Dict[str, Any]]] = None, storage: Optional[ReleaseStorage] = None) -> None:
        self.studio_name = studio_name
        self._raw_mock_data = raw_mock_data
        self.storage = storage or ReleaseStorage()

    @retry_on_failure(retries=3, delay=1.0)
    @log_execution
    def fetch_releases(self) -> Dict[str, Dict[str, Any]]:
        grouped_releases: Dict[str, Dict[str, Any]] = {}
        items = self._raw_mock_data if self._raw_mock_data is not None else []
        
        for item in items:
            media_type = item.get("media_type", "movie").lower().strip()
            title = item.get("title", "Unknown Studio Release")
            key = ReleaseStorage.normalize_key(media_type, title)
            category = f"{media_type}-releases"
            
            if key not in grouped_releases:
                grouped_releases[key] = {
                    "title": title,
                    "category": category,
                    "type": media_type,
                    "episodes": {} if media_type == "tv" else None
                }
            
            if media_type == "tv":
                season = item.get("season", 1)
                episode = item.get("episode", 1)
                ep_key = f"s{season:02d}e{episode:02d}"
                ep_name = item.get("episode_name", f"Episode {episode}")
                
                grouped_releases[key]["episodes"][ep_key] = {
                    "episode_name": ep_name,
                    "date": item.get("release_date", "2026-12-31"),
                    "synced": False
                }
            else:
                grouped_releases[key]["date"] = item.get("release_date", "2026-12-31")
                grouped_releases[key]["synced"] = False
                
        msg = f"Fetched {len(grouped_releases)} release groups for studio '{self.studio_name}'."
        logger.info(msg)
        self.storage.log_event(f"STUDIO_FETCH: {msg}")
        return grouped_releases
                      
