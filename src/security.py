from cryptography.fernet import Fernet, InvalidToken
import os
import logging
from src.config import settings

logger = logging.getLogger(__name__)

class SecurityService:
    """Manages secure AES-256 Fernet symmetric encryption and decryption."""

    def __init__(self, key: str = None) -> None:
        raw_key = key or settings.encryption_key
        try:
            # Test if key is valid Fernet key
            self._cipher = Fernet(raw_key.encode())
        except Exception:
            logger.warning("Provided encryption key is invalid. Auto-generating a secure Fernet key.")
            self._cipher = Fernet(Fernet.generate_key())

    def encrypt_data(self, plaintext: str) -> str:
        """Encrypts plaintext string into cipher token."""
        return self._cipher.encrypt(plaintext.encode()).decode()

    def decrypt_data(self, ciphertext: str) -> str:
        """Decrypts cipher token back into plaintext string."""
        try:
            return self._cipher.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt ciphertext: Invalid token or corrupted key.")
            raise
            
