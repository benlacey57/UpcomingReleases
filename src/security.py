import base64
import logging
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from src.config import settings

logger = logging.getLogger(__name__)

class SecurityService:
    """Handles AES-256 Fernet encryption with password-based key derivation (PBKDF2)."""
    
    SALT = b"release_calendar_sync_static_salt_v1"

    def __init__(self, key: str = None) -> None:
        self._key = key or settings.encryption_key
        try:
            self._cipher = Fernet(self._key.encode())
        except Exception as e:
            logger.error(f"Invalid encryption key provided: {e}")
            raise ValueError("Provided encryption key is invalid for Fernet initialization.")

    @classmethod
    def from_password(cls, password: str) -> "SecurityService":
        """Generates a SecurityService instance derived from a user-supplied password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=cls.SALT,
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return cls(key.decode())

    def encrypt_data(self, plaintext: str) -> str:
        """Encrypts plaintext string into a secure ciphertext token."""
        if not plaintext:
            return ""
        return self._cipher.encrypt(plaintext.encode()).decode()

    def decrypt_data(self, ciphertext: str) -> str:
        """Decrypts ciphertext token back into original plaintext string."""
        if not ciphertext:
            return ""
        try:
            return self._cipher.decrypt(ciphertext.encode()).decode()
        except InvalidToken as e:
            logger.error(f"Decryption failed due to invalid token or altered password/key: {e}")
            raise ValueError("Decryption failed. The token is invalid or the password is incorrect.")
