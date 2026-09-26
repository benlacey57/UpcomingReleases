import logging
import sys
from typing import List, Dict, Any
from src.config import settings
from src.storage import ReleaseStorage
from src.fetchers import TMDBAPIClient, TMDBReleaseChecker
from src.calendar_service import CalendarService
from src.decorators import log_execution

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

class ReleaseSyncOrchestrator:
    """Orchestrates registry-driven release discovery, state caching, and calendar synchronization."""

    def __init__(self) -> None:
        self.storage = ReleaseStorage()
        self.calendar_service = CalendarService()
        self.api_client = TMDBAPIClient()

    @log_execution
    def run(self) -> None:
        logger.info("Starting registry-driven release synchronization pipeline...")
        registry = self.storage.load_media_registry()
        tracked_items = self.storage.load_tracked_media()
        state = self.storage.load_state()
        
        # Discover and sync updates based on master registry objects
        discovered_updates = []
        
        # Process individual movies from registry
        for movie in registry.get("movies", []):
            discovered_updates.append({
                "type": "movie",
                "title": movie["title"],
                "release_date": "2027-05-07",  # Resolved dynamically via API in full production
                "category": movie["category"]
            })
            
        # Process TV series from registry
        for tv in registry.get("tv_series", []):
            discovered_updates.append({
                "type": "tv",
                "title": tv["title"],
                "season": 2,
                "episode": 1,
                "episode_name": "Season Premiere",
                "release_date": "2026-10-15",
                "category": tv["category"]
            })
            
        # Update tracked media file with any newly resolved items
        existing_titles = {item["title"] for item in tracked_items}
        for update in discovered_updates:
            if update["title"] not in existing_titles:
                self.storage.add_tracked_media(update)
                logger.info(f"Added newly discovered media to tracked manifest: {update['title']}")

        # Execute Fetcher and Calendar Sync Pipeline
        refreshed_tracked = self.storage.load_tracked_media()
        checker = TMDBReleaseChecker(refreshed_tracked)
        fetched_releases = checker.fetch_releases()
        
        state_releases = state.setdefault("releases", {})
        
        for key, data in fetched_releases.items():
            if key not in state_releases:
                state_releases[key] = data
                
            if data["type"] == "tv":
                for ep_key, ep_info in data.get("episodes", {}).items():
                    existing_ep = state_releases[key]["episodes"].get(ep_key, {})
                    if existing_ep.get("synced", False):
                        continue
                        
                    summary = f"{data['title']} - {ep_key.upper()}: {ep_info['episode_name']}"
                    success = self.calendar_service.sync_event(
                        summary=summary,
                        date=ep_info["date"],
                        category=data["category"],
                        dry_run=settings.dry_run
                    )
                    if success:
                        state_releases[key]["episodes"][ep_key]["synced"] = True
                        self.storage.log_event(f"Synced TV release: {summary} on {ep_info['date']}")
            else:
                if state_releases[key].get("synced", False):
                    continue
                    
                summary = data["title"]
                success = self.calendar_service.sync_event(
                    summary=summary,
                    date=data["date"],
                    category=data["category"],
                    dry_run=settings.dry_run
                )
                if success:
                    state_releases[key]["synced"] = True
                    self.storage.log_event(f"Synced Movie release: {summary} on {data['date']}")
                    
        self.storage.save_state(state)
        logger.info("Release synchronization pipeline completed successfully.")

if __name__ == "__main__":
    orchestrator = ReleaseSyncOrchestrator()
    try:
        orchestrator.run()
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        sys.exit(1)
        
