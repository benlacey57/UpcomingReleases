import argparse
import os
import sys
import logging
from src.config import settings
from src.storage import ReleaseStorage
from src.security import SecurityService
from src.calendar_service import CalendarService
from src.setup import SetupAssistant
from src.main import ReleaseSyncOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

class CLIController:
    """Manages command-line arguments and dispatches tasks."""

    def __init__(self) -> None:
        self.parser = argparse.ArgumentParser(
            description="Release Calendar Sync CLI: Manage tracking, syncing, and integration testing."
        )
        self.parser.add_argument("--setup", action="store_true", help="Run the interactive setup assistant.")
        self.parser.add_argument("--sync", action="store_true", help="Run the release synchronization pipeline.")
        self.parser.add_argument("--dry-run", action="store_true", help="Simulate actions without pushing live updates.")
        self.parser.add_argument("--list-movies", action="store_true", help="List all tracked and cached movies.")
        self.parser.add_argument("--list-series", action="store_true", help="List all tracked and cached TV series and episodes.")
        self.parser.add_argument("--show-logs", action="store_true", help="Display recent execution audit logs.")
        self.parser.add_argument("--test", action="store_true", help="Test API integrations and system status.")

    def execute(self) -> None:
        args = self.parser.parse_args()

        if args.setup:
            SetupAssistant.run_setup()
            return

        storage = ReleaseStorage()

        if args.list_movies:
            state = storage.load_state()
            print("\n--- Tracked Movies ---")
            found = False
            for key, data in state.get("releases", {}).items():
                if data.get("type") == "movie":
                    found = True
                    status = "Synced" if data.get("synced") else "Pending"
                    print(f"[{status}] {data['title']} (Release: {data.get('date')})")
            if not found:
                print("No movies currently tracked.")
            return

        if args.list_series:
            state = storage.load_state()
            print("\n--- Tracked TV Series & Episodes ---")
            found = False
            for key, data in state.get("releases", {}).items():
                if data.get("type") == "tv":
                    found = True
                    print(f"\nSeries: {data['title']} ({key})")
                    for ep_key, ep_info in data.get("episodes", {}).items():
                        ep_status = "Synced" if ep_info.get("synced") else "Pending"
                        print(f"  └─ [{ep_status}] {ep_key.upper()}: {ep_info['episode_name']} ({ep_info['date']})")
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
            print("\n--- Running Integration & System Tests ---")
            try:
                security = SecurityService()
                test_token = security.encrypt_data("ping-test")
                assert security.decrypt_data(test_token) == "ping-test"
                print(" [PASS] Security Encryption Service")

                calendar_service = CalendarService()
                assert calendar_service.calendar_id is not None
                print(" [PASS] Calendar Service Configuration")

                storage.load_state()
                print(" [PASS] Local Storage and State Access")
                print("\nAll integration checks passed successfully!")
            except Exception as e:
                print(f" [FAIL] Integration test failed: {e}")
                sys.exit(1)
            return

        if args.sync:
            if args.dry_run:
                settings.dry_run = True
                print("Executing synchronization in DRY-RUN mode...")
            else:
                settings.dry_run = False
                print("Executing LIVE synchronization...")
            
            orchestrator = ReleaseSyncOrchestrator()
            orchestrator.run()
            return

        self.parser.print_help()

if __name__ == "__main__":
    controller = CLIController()
    controller.execute()
            
