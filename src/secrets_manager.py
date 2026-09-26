import argparse
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class GitHubSecretsManager:
    """Manages GitHub repository secrets using the GitHub CLI (gh)."""

    @staticmethod
    def run_command(cmd: list[str]) -> None:
        try:
            result = subprocess.run(cmd, check=True, text=True, capture_output=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr.strip()}")
            sys.exit(1)
        except FileNotFoundError:
            logger.error("GitHub CLI ('gh') is not installed or not found in PATH. Please install it via https://cli.github.com/")
            sys.exit(1)

    @classmethod
    def list_secrets(cls) -> None:
        logger.info("Listing repository secrets...")
        cls.run_command(["gh", "secret", "list"])

    @classmethod
    def add_secret(cls, name: str, value: str) -> None:
        if not name or not value:
            logger.error("Both secret name and value are required.")
            sys.exit(1)
        logger.info(f"Setting secret '{name}'...")
        # Pass secret via stdin to prevent exposure in shell history
        process = subprocess.Popen(["gh", "secret", "set", name], stdin=subprocess.PIPE, text=True)
        process.communicate(input=value)
        if process.returncode == 0:
            logger.info(f"Successfully set secret '{name}'.")
        else:
            logger.error(f"Failed to set secret '{name}'.")
            sys.exit(1)

    @classmethod
    def delete_secret(cls, name: str) -> None:
        if not name:
            logger.error("Secret name is required for deletion.")
            sys.exit(1)
        logger.info(f"Deleting secret '{name}'...")
        cls.run_command(["gh", "secret", "remove", name])

def main() -> None:
    parser = argparse.ArgumentParser(description="Manage GitHub repository secrets.")
    parser.add_argument("--list", action="store_true", help="List all repository secrets")
    parser.add_argument("--add", action="store_true", help="Add or update a secret")
    parser.add_argument("--delete", action="store_true", help="Delete a secret")
    parser.add_argument("--name", type=str, help="Name of the secret")
    parser.add_argument("--value", type=str, help="Value of the secret")

    args = parser.parse_args()

    if args.list:
        GitHubSecretsManager.list_secrets()
    elif args.add:
        name = args.name or input("Enter secret name: ").strip()
        value = args.value or input("Enter secret value: ").strip()
        GitHubSecretsManager.add_secret(name, value)
    elif args.delete:
        name = args.name or input("Enter secret name to delete: ").strip()
        GitHubSecretsManager.delete_secret(name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
  
