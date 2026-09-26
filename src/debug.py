import os
import sys
import json
import logging
import importlib.metadata
from datetime import datetime, timezone
from cryptography.fernet import Fernet
import zoneinfo

from src.config import settings
from src.storage import ReleaseStorage
from src.security import SecurityService
from src.calendar_service import CalendarService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

class SystemDiagnostics:
    """Performs end-to-end system health checks and generates a detailed audit report."""

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
        self.report_lines.append(f"Release Calendar Sync - System Diagnostic Report\nGenerated at: {timestamp}\n")
        
        all_passed = True

        # 1. Environment & Settings Check
        self._log_section("1. Environment & Configuration Check")
        try:
            assert settings.calendar_id, "Calendar ID is missing."
            self._log_line(f"Calendar ID: {settings.calendar_id}", "PASS")
            
            zoneinfo.ZoneInfo(settings.timezone)
            self._log_line(f"Timezone: {settings.timezone} (Valid)", "PASS")
            
            self._log_line(f"Dry Run Mode: {settings.dry_run}", "INFO")
            self._log_line(f"Calendar Sync Enabled: {settings.enable_calendar_sync}", "INFO")
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

        # 3. Filesystem & Storage Check
        self._log_section("3. Filesystem & Storage Check")
        try:
            storage = ReleaseStorage()
            state = storage.load_state()
            cache = storage.load_cache()
            tracked = storage.load_tracked_media()
            storage.log_event("DIAGNOSTIC: System debug check executed.")
            
            self._log_line(f"State file accessible ({len(state.get('releases', {}))} entries).", "PASS")
            self._log_line(f"Cache file accessible ({len(cache.get('cached_releases', {}))} entries).", "PASS")
            self._log_line(f"Tracked media file accessible ({len(tracked)} items).", "PASS")
            self._log_line("Log writing and directory permissions verified.", "PASS")
        except Exception as e:
            self._log_line(f"Storage validation failed: {e}", "FAIL")
            all_passed = False

        # 4. Dependency Versions Check
        self._log_section("4. Python Dependencies Check")
        required_packages = ["google-api-python-client", "google-auth", "cryptography", "pydantic", "pytest", "requests"]
        for pkg in required_packages:
            try:
                version = importlib.metadata.version(pkg)
                self._log_line(f"Package '{pkg}' installed (Version: {version})", "PASS")
            except importlib.metadata.PackageNotFoundError:
                self._log_line(f"Package '{pkg}' is NOT installed.", "FAIL")
                all_passed = False

        # 5. Google Calendar API Authentication Check
        self._log_section("5. Google Calendar API Connectivity Check")
        try:
            calendar_service = CalendarService()
            if settings.google_credentials_json in ("{}", "", None):
                self._log_line("Google credentials JSON is empty or unconfigured. Skipping live API call (Dry-Run active).", "WARN")
            else:
                calendars = calendar_service.fetch_user_calendars()
                self._log_line(f"Successfully authenticated and retrieved {len(calendars)} calendar(s).", "PASS")
                for cal in calendars:
                    self._log_line(f"  └─ Calendar: {cal.get('summary')} (ID: {cal.get('id')})", "INFO")
        except Exception as e:
            self._log_line(f"Google Calendar authentication or API check failed: {e}", "FAIL")
            all_passed = False

        # Write Report
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.report_lines))

        self._log_section("Summary")
        if all_passed:
            self._log_line(f"All diagnostic checks passed successfully! Report saved to {self.report_path}", "PASS")
        else:
            self._log_line(f"Some checks failed. Review details in {self.report_path}", "FAIL")
            sys.exit(1)

        return all_passed

if __name__ == "__main__":
    diagnostic = SystemDiagnostics()
    diagnostic.run_checks()
      
