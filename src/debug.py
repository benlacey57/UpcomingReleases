import os
import sys
import json
import logging
import importlib.metadata
from datetime import datetime, timezone, date
import zoneinfo
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import settings
from src.storage import ReleaseStorage
from src.security import SecurityService
from src.calendar_service import CalendarService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

class SystemDiagnostics:
    """Performs rigorous end-to-end system health checks, storage verification, and live calendar permission tests."""

    def __init__(self, report_path: str = "logs/debug_report.txt") -> None:
        self.report_path = report_path
        os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
        self.report_lines: list[str] = []

    def _log_section(self, title: str) -> None:
        header = f"\n{'='*50}\n{title}\n{'='*50}"
        print(header)
        self.report_lines.append(header)

    def _log_line(self, message: str, status: str = "INFO") -> None:
        formatted = f"[{status}] {message}"
        print(formatted)
        self.report_lines.append(formatted)

    def run_checks(self) -> bool:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        self.report_lines.append(f"Release Calendar Sync - Advanced System Diagnostic Report\nGenerated at: {timestamp}\n")
        
        all_passed = True

        # 1. Environment & Settings Check
        self._log_section("1. Environment & Configuration Check")
        try:
            assert settings.calendar_id, "Calendar ID is missing."
            self._log_line(f"Calendar ID: {settings.calendar_id}", "PASS")
            
            zoneinfo.ZoneInfo(settings.timezone)
            self._log_line(f"Timezone: {settings.timezone} (Valid)", "PASS")
            
            self._log_line(f"Dry Run Mode: {settings.dry_run}", "INFO")
        except Exception as e:
            self._log_line(f"Configuration validation failed: {e}", "FAIL")
            all_passed = False

        # 2. Security & Encryption Key Check
        self._log_section("2. Security & Encryption Check")
        try:
            security = SecurityService()
            test_token = security.encrypt_data("diagnostic-ping")
            decrypted = security.decrypt_data(test_token)
            assert decrypted == "diagnostic-ping"
            self._log_line("Encryption key is valid and Fernet cipher initialized successfully.", "PASS")
        except Exception as e:
            self._log_line(f"Security validation failed: {e}", "FAIL")
            all_passed = False

        # 3. Filesystem & Rigorous Storage Check
        self._log_section("3. Filesystem & Storage Integrity Check")
        try:
            storage = ReleaseStorage()
            
            # Test State CRUD Roundtrip
            test_state = {"releases": {"test:diagnostic-item": {"title": "Diagnostic Test", "synced": True}}}
            storage.save_state(test_state)
            loaded_state = storage.load_state()
            assert loaded_state["releases"]["test:diagnostic-item"]["title"] == "Diagnostic Test"
            self._log_line("State storage read/write roundtrip verified.", "PASS")

            # Test Cache CRUD Roundtrip
            test_cache = {"last_updated": timestamp, "cached_releases": {}}
            storage.save_cache(test_cache)
            loaded_cache = storage.load_cache()
            assert loaded_cache["last_updated"] == timestamp
            self._log_line("Cache storage read/write roundtrip verified.", "PASS")

            # Test Tracked Media CRUD
            storage.save_tracked_media([{"type": "movie", "title": "Diagnostic Movie", "release_date": "2027-01-01"}])
            tracked = storage.load_tracked_media()
            assert len(tracked) == 1
            storage.remove_tracked_item("Diagnostic Movie", "movie")
            self._log_line("Tracked media CRUD operations verified.", "PASS")

            storage.log_event("DIAGNOSTIC: Full storage integrity check passed.")
        except Exception as e:
            self._log_line(f"Storage integrity check failed: {e}", "FAIL")
            all_passed = False

        # 4. Python Dependencies Check
        self._log_section("4. Python Dependencies Check")
        required_packages = ["google-api-python-client", "google-auth", "cryptography", "pydantic", "pytest", "requests"]
        for pkg in required_packages:
            try:
                version = importlib.metadata.version(pkg)
                self._log_line(f"Package '{pkg}' installed (Version: {version})", "PASS")
            except importlib.metadata.PackageNotFoundError:
                self._log_line(f"Package '{pkg}' is NOT installed.", "FAIL")
                all_passed = False

        # 5. Live Google Calendar Permissions Test (Read, Write, Delete)
        self._log_section("5. Google Calendar Permissions & Live API Test")
        calendar_service = CalendarService()
        if settings.google_credentials_json in ("{}", "", None):
            self._log_line("Google credentials JSON is unconfigured. Skipping live API permission test (Dry-Run active).", "WARN")
        else:
            try:
                # Test Read Access (List Calendars & Events)
                calendars = calendar_service.fetch_user_calendars()
                self._log_line(f"Calendar READ Access: SUCCESS ({len(calendars)} calendars accessible).", "PASS")

                service = build("calendar", "v3", credentials=calendar_service._credentials)
                
                # Test Read Events on target calendar
                service.events().list(calendarId=calendar_service.calendar_id, maxResults=1).execute()
                self._log_line(f"Calendar ID '{calendar_service.calendar_id}' read check: SUCCESS.", "PASS")

                # Test Write Access (Insert temporary test event)
                today_str = date.today().isoformat()
                test_event_body = {
                    "summary": "[DIAGNOSTIC TEST] Temporary Permission Check",
                    "start": {"date": today_str},
                    "end": {"date": today_str},
                    "description": "Automated diagnostic permissions check. Will be deleted instantly."
                }
                
                created_event = service.events().insert(calendarId=calendar_service.calendar_id, body=test_event_body).execute()
                event_id = created_event.get("id")
                self._log_line(f"Calendar WRITE Access: SUCCESS (Inserted test event ID: {event_id})", "PASS")

                # Test Delete Access (Clean up test event immediately)
                service.events().delete(calendarId=calendar_service.calendar_id, eventId=event_id).execute()
                self._log_line("Calendar DELETE / Cleanup Access: SUCCESS (Test event successfully removed)", "PASS")

            except HttpError as error:
                self._log_line(f"Google Calendar API permission test FAILED: {error}", "FAIL")
                self._log_line("Ensure your Service Account email has been shared with 'Make changes to events' permissions on this calendar.", "WARN")
                all_passed = False
            except Exception as e:
                self._log_line(f"Unexpected error during calendar permission check: {e}", "FAIL")
                all_passed = False

        # Write Report
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.report_lines))

        self._log_section("Summary")
        if all_passed:
            self._log_line(f"All diagnostic and calendar permission checks passed successfully! Report saved to {self.report_path}", "PASS")
        else:
            self._log_line(f"Some checks failed. Review details in {self.report_path}", "FAIL")
            sys.exit(1)

        return all_passed

if __name__ == "__main__":
    diagnostic = SystemDiagnostics()
    diagnostic.run_checks()
    
