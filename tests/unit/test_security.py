import pytest
from src.security import SecurityService

def test_encryption_decryption_roundtrip():
    key = SecurityService()._key
    service = SecurityService(key)
    plaintext = "super-secret-api-token"
    
    ciphertext = service.encrypt_data(plaintext)
    assert ciphertext != plaintext
    
    decrypted = service.decrypt_data(ciphertext)
    assert decrypted == plaintext

def test_invalid_encryption_key():
    with pytest.raises(ValueError):
        SecurityService("invalid-key")

def test_invalid_token_decryption():
    service = SecurityService()
    with pytest.raises(ValueError):
        service.decrypt_data("not-a-valid-fernet-token")
      
