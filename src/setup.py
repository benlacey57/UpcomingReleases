import os
import subprocess
import sys
import logging
from src.storage import ReleaseStorage

logger = logging.getLogger(__name__)

class SetupAssistant:
    """Guides non-technical users through environment setup and API credential configuration."""

    @staticmethod
    def run_setup() -> None:
        print("\n=== Release Calendar Sync: Interactive Setup Assistant ===")
        print("This wizard will help you set up your environment, virtual environment, and credentials.\n")

        # 1. Virtual Environment & Dependencies
        print("[1/3] Setting up Python virtual environment and installing dependencies...")
        if not os.path.exists(".venv"):
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            print(" -> Created virtual environment (.venv).")
        else:
            print(" -> Virtual environment already exists.")

        pip_path = os.path.join(".venv", "bin", "pip") if os.name != "nt" else os.path.join(".venv", "Scripts", "pip.exe")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print(" -> Dependencies successfully installed.\n")

        # 2. Configuration & Credentials
        print("[2/3] Configuring API Keys and Secrets...")
        existing_key = os.getenv("ENCRYPTION_KEY", "insecure-default-key-for-testing==")
        encryption_key = input(f"Enter Encryption Key [Default/Auto]: ").strip() or existing_key
        calendar_id = input(f"Enter Google Calendar ID [Default: primary]: ").strip() or "primary"
        
        print("\nGoogle Service Account JSON Credentials:")
        google_creds = input("Google Credentials JSON (single-line or press Enter to skip): ").strip() or "{}"

        env_content = f"""ENCRYPTION_KEY={encryption_key}
CALENDAR_ID={calendar_id}
GOOGLE_CREDENTIALS_JSON='{google_creds}'
DRY_RUN=true
ENABLE_CALENDAR_SYNC=true
ENABLE_GIT_COMMIT=false
ENABLE_API_FETCH=true
"""
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print(" -> Configuration saved to .env successfully.\n")

        # 3. Directory Structure
        print("[3/3] Initializing local storage directories...")
        storage = ReleaseStorage()
        storage.save_state({"releases": {}})
        storage.save_cache({"last_updated": "", "cached_releases": {}})
        storage.log_event("Setup assistant initialized storage successfully.")
        print(" -> Storage and logs initialized.\n")
        print("Setup complete! You can now run tests with: make test")
      
