import os
import glob
import json
import subprocess
import sys
import shutil
import logging
from src.storage import ReleaseStorage
from src.security import SecurityService

logger = logging.getLogger(__name__)

class SetupAssistant:
    """Guides users through environment provisioning, service account detection, and .env creation."""

    @staticmethod
    def run_setup() -> None:
        print("\n=== Release Calendar Sync: Secure Setup Assistant ===")
        print("This wizard will provision your environment, check for local service account files, and configure your .env file.\n")

        # 1. Virtual Environment & Dependencies
        print("[1/4] Setting up Python virtual environment and dependencies...")
        if not os.path.exists(".venv"):
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            print(" -> Created virtual environment (.venv).")
        else:
            print(" -> Virtual environment already exists.")

        pip_path = os.path.join(".venv", "bin", "pip") if os.name != "nt" else os.path.join(".venv", "Scripts", "pip.exe")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print(" -> Dependencies successfully installed.\n")

        # 2. Service Account JSON Detection & Password Encryption
        print("[2/4] Inspecting project root for Google Service Account JSON files...")
        json_files = glob.glob("*.json")
        service_account_json = "{}"
        detected_file = None

        for file in json_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("type") == "service_account" and "private_key" in data:
                        detected_file = file
                        service_account_json = json.dumps(data)
                        break
            except Exception:
                continue

        if detected_file:
            print(f" -> Found Google Service Account file: '{detected_file}'")
            password = input("Enter a master password to encrypt your credentials (or press Enter to store unencrypted): ").strip()
            if password:
                security = SecurityService.from_password(password)
                encrypted_creds = security.encrypt_data(service_account_json)
                encryption_key = security._key
                print(" -> Credentials successfully encrypted.")
            else:
                encryption_key = os.getenv("ENCRYPTION_KEY", "insecure-default-key-for-testing==")
                encrypted_creds = service_account_json
                print(" -> No password provided. Storing unencrypted.")
        else:
            print(" -> No service account JSON found in root directory.")
            encryption_key = os.getenv("ENCRYPTION_KEY", "insecure-default-key-for-testing==")
            encrypted_creds = input("Paste your Google Credentials JSON string (or press Enter to skip): ").strip() or "{}"

        calendar_id = input("Enter Google Calendar ID [Default: primary]: ").strip() or "primary"
        timezone = input("Enter Timezone [Default: UTC]: ").strip() or "UTC"

        # 3. Create or Update .env from .env.example
        print("\n[3/4] Generating .env configuration file...")
        if not os.path.exists(".env") and os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print(" -> Created .env from .env.example template.")

        env_content = f"""ENCRYPTION_KEY={encryption_key}
CALENDAR_ID={calendar_id}
TIMEZONE={timezone}
GOOGLE_CREDENTIALS_JSON='{encrypted_creds}'
DRY_RUN=true
ENABLE_CALENDAR_SYNC=true
ENABLE_GIT_COMMIT=false
ENABLE_API_FETCH=true
"""
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print(" -> .env file updated successfully.")

        if detected_file:
            confirm_delete = input(f"\nWould you like to securely delete the raw local file '{detected_file}'? (y/N): ").strip().lower()
            if confirm_delete == 'y':
                os.remove(detected_file)
                print(f" -> Successfully deleted raw file '{detected_file}'.")
            else:
                print(f" -> WARNING: Raw file '{detected_file}' retained. Ensure it is added to .gitignore!")

        # 4. GitHub Secrets Integration
        print("\n[4/4] GitHub Secrets Integration Check...")
        has_gh_cli = subprocess.run(["gh", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        
        if has_gh_cli:
            push_secrets = input("GitHub CLI ('gh') detected. Push ENCRYPTION_KEY and GOOGLE_CREDENTIALS_JSON to GitHub Secrets? (y/N): ").strip().lower()
            if push_secrets == 'y':
                try:
                    subprocess.run(["gh", "secret", "set", "ENCRYPTION_KEY", "--body", encryption_key], check=True)
                    subprocess.run(["gh", "secret", "set", "GOOGLE_CREDENTIALS_JSON", "--body", encrypted_creds], check=True)
                    subprocess.run(["gh", "secret", "set", "CALENDAR_ID", "--body", calendar_id], check=True)
                    print(" -> Successfully synced secrets to GitHub!")
                except Exception as e:
                    print(f" -> Failed to push secrets via GitHub CLI: {e}")
        else:
            print(" -> GitHub CLI not detected. You can manually add secrets to your repository settings.")

        # Initialize Storage
        storage = ReleaseStorage()
        storage.save_state({"releases": {}})
        storage.save_cache({"last_updated": "", "cached_releases": {}})
        storage.log_event("Setup assistant completed successfully.")
        print("\nSetup complete! You can verify your setup with: make debug")
                
