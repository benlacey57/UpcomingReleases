import logging
from typing import List, Dict, Any
from src.config import settings
from src.storage import ReleaseStorage
from src.fetchers import TMDBReleaseChecker
from src.calendar_service import CalendarService
from src.decorators import log_execution

logger = logging.getLogger(__name__)

class ReleaseSyncOrchestrator:
    """Orchestrates release checking, nested state caching, and calendar synchronization."""

    def __init__(self) -> None:
        self.storage = ReleaseStorage()
        self.calendar_service = CalendarService()

    @log_execution
    def run(self) -> None:
        logger.info("Starting release synchronization pipeline...")
        state = self.storage.load_state()
        cache = self.storage.load_cache()
        
        tracked_media: List[Dict[str, Any]] = [
            {"type": "tv", "title": "Breaking Bad", "season": 1, "episode": 1, "episode_name": "Pilot", "release_date": "2026-10-15"},
            {"type": "tv", "title": "Breaking Bad", "season": 1, "episode": 2, "episode_name": "Cat's in the Bag...", "release_date": "2026-10-22"},
            {"type": "movie", "title": "Action Hero Returns", "release_date": "2026-11-01"}
        ]
        
        checker = TMDBReleaseChecker(tracked_media)
        fetched_releases = checker.fetch_releases()
        
        state_releases = state.setdefault("releases", {})
        cache_releases = cache.setdefault("cached_releases", {})
        
        for key, data in fetched_releases.items():
            if key not in state_releases:
                state_releases[key] = data
            if key not in cache_releases:
                cache_releases[key] = data
                
            if data["type"] == "tv":
                for ep_key, ep_info in data["episodes"].items():
                    existing_ep = state_releases[key]["episodes"].get(ep_key, {})
                    if existing_ep.get("synced", False):
                        logger.info(f"Skipping already synced episode: {key} {ep_key}")
                        continue
                        
                    summary = f"{data['title']} - {ep_key.upper()}: {ep_info['episode_name']}"
                    success = self.calendar_service.sync_event(
                        summary=summary,
                        date_str=ep_info["date"],
                        category=data["category"],
                        dry_run=settings.dry_run
                    )
                    
                    if success:
                        state_releases[key]["episodes"][ep_key]["synced"] = True
                        cache_releases[key]["episodes"][ep_key]["synced"] = True
                        self.storage.log_event(f"Synced TV release: {summary} on {ep_info['date']}")
            else:
                if state_releases[key].get("synced", False):
                    logger.info(f"Skipping already synced movie: {key}")
                    continue
                    
                summary = data["title"]
                success = self.calendar_service.sync_event(
                    summary=summary,
                    date_str=data["date"],
                    category=data["category"],
                    dry_run=settings.dry_run
                )
                
                if success:
                    state_releases[key]["synced"] = True
                    cache_releases[key]["synced"] = True
                    self.storage.log_event(f"Synced Movie release: {summary} on {data['date']}")
                    
        self.storage.save_state(state)
        self.storage.save_cache(cache)
        logger.info("Release synchronization pipeline completed successfully.")

if __name__ == "__main__":
    import sys
    orchestrator = ReleaseSyncOrchestrator()
    try:
        orchestrator.run()
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        sys.exit(1)
                
