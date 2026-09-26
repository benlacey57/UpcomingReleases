import abc
import logging
import requests
import os
from typing import List, Dict, Any, Optional
from src.decorators import log_execution, retry_on_failure
from src.storage import ReleaseStorage
from src.config import settings

logger = logging.getLogger(__name__)

class BaseReleaseChecker(abc.ABC):
    """Abstract Base Class for checking media release updates following SOLID principles."""

    @abc.abstractmethod
    def fetch_releases(self) -> Dict[str, Dict[str, Any]]:
        """Fetches upcoming releases grouped by parent media key."""
        pass

class TMDBAPIClient:
    """Handles communication with the TMDB API for searching movies, TV shows, and studios."""
    
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("TMDB_API_KEY", "")
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}" if len(self.api_key) > 40 else ""
        }

    @retry_on_failure(retries=3, delay=1.0)
    @log_execution
    def search_media(self, query: str, media_type: str) -> List[Dict[str, Any]]:
        """Searches TMDB for movies or TV shows matching the query."""
        if not self.api_key or settings.dry_run:
            logger.info(f"[DRY-RUN / NO API KEY] Returning mock search results for {media_type}: '{query}'")
            return [
                {"id": 101, "title": f"{query} (2026)", "release_date": "2026-11-15"},
                {"id": 102, "title": f"{query}: Legacy (2027)", "release_date": "2027-05-20"}
            ]
            
        endpoint = f"{self.BASE_URL}/search/{media_type}"
        params = {"query": query, "include_adult": False, "language": "en-US", "page": 1}
        
        if "Authorization" in self.headers and self.headers["Authorization"]:
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=10)
        else:
            params["api_key"] = self.api_key
            response = requests.get(endpoint, params=params, timeout=10)
            
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        
        formatted = []
        for item in results:
            title = item.get("title") or item.get("name") or "Unknown"
            date = item.get("release_date") or item.get("first_air_date") or "2026-12-31"
            formatted.append({"id": item.get("id"), "title": title, "release_date": date})
        return formatted

    @log_execution
    def search_studio(self, studio_name: str) -> List[Dict[str, Any]]:
        """Searches TMDB for production companies/studios."""
        if not self.api_key or settings.dry_run:
            return [{"id": 420, "name": studio_name}]
            
        endpoint = f"{self.BASE_URL}/search/company"
        params = {"query": studio_name, "page": 1}
        if "Authorization" in self.headers and self.headers["Authorization"]:
            response = requests.get(endpoint, headers=self.headers, params=params, timeout=10)
        else:
            params["api_key"] = self.api_key
            response = requests.get(endpoint, params=params, timeout=10)
            
        response.raise_for_status()
        return response.json().get("results", [])


class TMDBReleaseChecker(BaseReleaseChecker):
    """Concrete implementation for fetching specific watchlist release updates."""

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


class StudioReleaseChecker(BaseReleaseChecker):
    """Dedicated studio/franchise catalog checker handling mixed media types."""

    def __init__(self, studio_name: str, raw_mock_data: Optional[List[Dict[str, Any]]] = None) -> None:
        self.studio_name = studio_name
        self._raw_mock_data = raw_mock_data

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
                
        return grouped_releases
