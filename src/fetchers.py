import abc
import logging
from typing import List, Dict, Any
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
    """Concrete implementation for fetching release updates with nested episode mapping."""

    def __init__(self, tracked_items: List[Dict[str, Any]]) -> None:
        self.tracked_items = tracked_items

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
                
        return grouped_releases
                  
