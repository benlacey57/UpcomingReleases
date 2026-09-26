import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from src.config import settings
from src.storage import ReleaseStorage
from src.fetchers import TMDBReleaseChecker
from src.calendar_service import CalendarService
from src.decorators import log_execution

logger = logging.getLogger(__name__)

class ReleaseSyncOrchestrator:
    """Orchestrates syncing, untrack cleanup, and category event tracking."""

    def __init__(self) -> None:
        self.storage = ReleaseStorage()
        self.calendar_service = CalendarService()

    @log_execution
    def run(self) -> None:
        logger.info("Starting release synchronization pipeline...")
        state = self.storage.load_state()
        cache = self.storage.load_cache()
        tracked_media = self.storage.load_tracked_media()
        
        # Default seed if empty
        if not tracked_media:
            tracked_media = [
                {"type": "tv", "title": "Breaking Bad", "season": 1, "episode": 1, "episode_name": "Pilot", "release_date": "2026-10-15"},
                {"type": "movie", "title": "Thunderbolts", "studio": "Marvel", "release_date": "2027-05-01"}
            ]
            self.storage.save_tracked_media(tracked_media)

        state_releases = state.setdefault("releases", {})
        
        # 1. Handle Untracked Items Cleanup (Soft-Delete & Calendar Removal)
        tracked_keys = {ReleaseStorage.normalize_key(i["type"], i["title"]) for i in tracked_media}
        for existing_key, data in list(state_releases.items()):
            if existing_key not in tracked_keys and not data.get("deleted_at"):
                logger.info(f"Detected untracked item: {existing_key}. Removing calendar events...")
                
                # Remove calendar events
                if data["type"] == "tv":
                    for ep_key, ep_info in data.get("episodes", {}).items():
                        summary = f"{data['title']} - {ep_key.upper()}: {ep_info['episode_name']}"
                        self.calendar_service.delete_event(summary, data["category"], settings.dry_run)
                else:
                    self.calendar_service.delete_event(data["title"], data["category"], settings.dry_run)
                
                # Mark as deleted with timestamp
                data["deleted_at"] = datetime.now(timezone.utc).isoformat()
                self.storage.log_event(f"DELETED: Untracked and removed calendar events for {data['title']}")

        # 2. Fetch & Sync Active Tracked Items
        checker = TMDBReleaseChecker(tracked_media)
        fetched_releases = checker.fetch_releases()
        
        for key, data in fetched_releases.items():
            if key not in state_releases:
                state_releases[key] = data
                
            if data["type"] == "tv":
                for ep_key, ep_info in data["episodes"].items():
                    existing_ep = state_releases[key]["episodes"].get(ep_key, {})
                    if existing_ep.get("synced", False):
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
                        self.storage.log_event(f"Synced TV release: {summary} on {ep_info['date']}")
            else:
                if state_releases[key].get("synced", False):
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
                    self.storage.log_event(f"Synced Movie release: {summary} on {data['date']}")
                    
        self.storage.save_state(state)
        self.storage.save_cache(cache)
        logger.info("Synchronization and cleanup pipeline completed successfully.")

if __name__ == "__main__":
    import sys
    orchestrator = ReleaseSyncOrchestrator()
    try:
        orchestrator.run()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
                
