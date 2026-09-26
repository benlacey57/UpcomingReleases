import logging
from cryptography.fernet import Fernet, InvalidToken
from src.config import settings

logger = logging.getLogger(__name__)

class SecurityService:
    """Handles AES-256 Fernet symmetric encryption and decryption for sensitive data."""
    
    def __init__(self, key: str = None) -> None:
        self._key = key or settings.encryption_key
        try:
            self._cipher = Fernet(self._key.encode())
        except Exception as e:
            logger.error(f"Invalid encryption key provided: {e}")
            raise ValueError("Provided encryption key is invalid for Fernet initialization.")

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
            logger.error(f"Decryption failed due to invalid token or altered key: {e}")
            raise ValueError("Decryption failed. The token is invalid or corrupted.")
          
