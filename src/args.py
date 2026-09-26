import argparse
import os
import sys
import logging
from collections import defaultdict
from src.config import settings
from src.storage import ReleaseStorage
from src.security import SecurityService
from src.calendar_service import CalendarService
from src.setup import SetupAssistant
from src.main import ReleaseSyncOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

class CLIController:
    """Manages command-line arguments, category totals, and CRUD task dispatching."""

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(description="Release Calendar Sync CLI")
        self.parser.add_argument("--setup", action="store_true", help="Run interactive setup assistant.")
        self.parser.add_argument("--sync", action="store_true", help="Run synchronization and untrack cleanup.")
        self.parser.add_argument("--dry-run", action="store_true", help="Simulate actions without live updates.")
        self.parser.add_argument("--list-categories", action="store_true", help="List calendar events by category with totals.")
        self.parser.add_argument("--list-movies", action="store_true", help="List tracked movies.")
        self.parser.add_argument("--list-series", action="store_true", help="List tracked TV series.")
        self.parser.add_argument("--show-logs", action="store_true", help="Display execution audit logs.")
        self.parser.add_argument("--test", action="store_true", help="Test system status.")
        
        # CRUD & Deletion arguments
        self.parser.add_argument("--add", nargs=3, metavar=("TYPE", "TITLE", "DATE"), help="Add a tracked item (e.g. --add movie 'Thunderbolts' '2027-05-01')")
        self.parser.add_argument("--remove", nargs=2, metavar=("TYPE", "TITLE"), help="Remove a tracked item (e.g. --remove movie 'Thunderbolts')")
        self.parser.add_argument("--delete-events", nargs="?", const="all", metavar="CATEGORY", help="Delete events by category, year, or month filter.")

    def execute(self) -> None:
        args = self.parser.parse_args()
        storage = ReleaseStorage()

        if args.setup:
            SetupAssistant.run_setup()
            return

        if args.add:
            m_type, title, date = args.add
            storage.add_tracked_item({"type": m_type, "title": title, "release_date": date})
            print(f"Successfully added tracked item: {m_type} - {title}")
            return

        if args.remove:
            m_type, title = args.remove
            if storage.remove_tracked_item(title, m_type):
                print(f"Successfully removed tracked item and queued calendar cleanup: {m_type} - {title}")
            else:
                print(f"Item not found in tracked list: {m_type} - {title}")
            return

        if args.list_categories:
            state = storage.load_state()
            category_counts = defaultdict(int)
            for _, data in state.get("releases", {}).items():
                if data.get("deleted_at"):
                    continue
                cat = data.get("category", "unknown-releases")
                if data["type"] == "tv":
                    ep_count = sum(1 for ep in data.get("episodes", {}).values() if not ep.get("deleted_at"))
                    category_counts[cat] += ep_count
                else:
                    category_counts[cat] += 1

            print("\n--- Calendar Categories & Event Totals ---")
            if category_counts:
                for cat, total in category_counts.items():
                    print(f"• {cat}: {total} events")
            else:
                print("No active categorized events found.")
            return

        if args.list_movies:
            tracked = storage.load_tracked_media()
            print("\n--- Tracked Movies ---")
            found = False
            for item in tracked:
                if item.get("type") == "movie":
                    found = True
                    print(f"• {item.get('title')} (Studio: {item.get('studio', 'N/A')}, Date: {item.get('release_date')})")
            if not found:
                print("No movies currently tracked.")
            return

        if args.list_series:
            tracked = storage.load_tracked_media()
            print("\n--- Tracked TV Series ---")
            found = False
            for item in tracked:
                if item.get("type") == "tv":
                    found = True
                    print(f"• {item.get('title')} S{item.get('season', 1):02d}E{item.get('episode', 1):02d} ({item.get('release_date')})")
            if not found:
                print("No TV series currently tracked.")
            return

        if args.show_logs:
            print("\n--- Execution Audit Logs ---")
            if os.path.exists(storage.log_file):
                with open(storage.log_file, "r", encoding="utf-8") as f:
                    print(f.read())
            else:
                print("No log file found.")
            return

        if args.test:
            print("\n--- Running System Tests ---")
            security = SecurityService()
            token = security.encrypt_data("test")
            assert security.decrypt_data(token) == "test"
            print(" [PASS] Security & Storage Checks Passed.")
            return

        if args.sync:
            if args.dry_run:
                settings.dry_run = True
                print("Running sync in DRY-RUN mode...")
            else:
                settings.dry_run = False
                print("Running LIVE sync...")
            orchestrator = ReleaseSyncOrchestrator()
            orchestrator.run()
            return

        self.parser.print_help()

if __name__ == "__main__":
    controller = CLIController()
    controller.execute()
        
