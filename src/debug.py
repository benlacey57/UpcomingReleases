import os
import sys
import logging
from src.config import settings
from src.security import SecurityService

# ANSI Color Codes for terminal formatting
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_status(component: str, status: str, message: str) -> None:
    if status == "PASS":
        color = GREEN
        symbol = "✔"
    elif status == "WARN":
        color = YELLOW
        symbol = "⚠"
    else:
        color = RED
        symbol = "✘"
    print(f"[{color}{symbol} {status}{RESET}] {BOLD}{component}{RESET}: {message}")

def run_debug_checks() -> int:
    print(f"\n{BOLD}=============================================={RESET}")
    print(f"{BOLD}      Release Tracker: Diagnostic Suite       {RESET}")
    print(f"{BOLD}=============================================={RESET}\n")
    
    failure_count = 0
    
    # 1. Environment & Configuration Check
    if os.path.exists(".env"):
        print_status("Configuration", "PASS", "'.env' file found.")
    else:
        print_status("Configuration", "WARN", "'.env' file missing. Using system environment variables.")

    # 2. Encryption Key Check
    try:
        security = SecurityService()
        test_msg = "diagnostic-test"
        encrypted = security.encrypt_data(test_msg)
        decrypted = security.decrypt_data(encrypted)
        if decrypted == test_msg:
            print_status("Encryption", "PASS", "AES-256 Fernet encryption and decryption functional.")
        else:
            print_status("Encryption", "FAIL", "Encryption/Decryption round-trip data mismatch.")
            failure_count += 1
    except Exception as e:
        print_status("Encryption", "FAIL", f"Security initialization failed: {e}")
        failure_count += 1

    # 3. TMDB API Key Check
    tmdb_key = os.getenv("TMDB_API_KEY_SECURE") or os.getenv("TMDB_API_KEY")
    if tmdb_key:
        print_status("TMDB API", "PASS", "TMDB API credentials detected.")
    else:
        print_status("TMDB API", "WARN", "TMDB API key not configured. Will use dry-run/mock fallback mode.")

    # 4. Google Calendar & Credentials Check
    cal_id = settings.calendar_id
    print_status("Google Calendar", "PASS", f"Target Calendar ID configured as: '{cal_id}'")
    
    creds_json = settings.google_credentials_json
    if creds_json and creds_json != "{}":
        print_status("Google Credentials", "PASS", "Google Service Account credentials provided.")
    else:
        print_status("Google Credentials", "WARN", "Google credentials unconfigured. Live API sync will be skipped.")

    # 5. Feature Flag State
    print(f"\n{BOLD}--- Feature Flag Status ---{RESET}")
    print_status("Dry Run Mode", "PASS" if settings.dry_run else "WARN", f"DRY_RUN = {settings.dry_run}")
    print_status("Calendar Sync", "PASS" if settings.enable_calendar_sync else "WARN", f"ENABLE_CALENDAR_SYNC = {settings.enable_calendar_sync}")
    print_status("Git Auto-Commit", "PASS" if settings.enable_git_commit else "WARN", f"ENABLE_GIT_COMMIT = {settings.enable_git_commit}")
    print_status("API Fetching", "PASS" if settings.enable_api_fetch else "WARN", f"ENABLE_API_FETCH = {settings.enable_api_fetch}")

    print(f"\n{BOLD}=============================================={RESET}")
    if failure_count == 0:
        print(f"{GREEN}{BOLD}All critical diagnostic checks passed successfully!{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}Diagnostics completed with {failure_count} critical failure(s).{RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(run_debug_checks())
            
