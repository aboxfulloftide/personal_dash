"""
Encryption utilities for sensitive data like email passwords.
Uses Fernet symmetric encryption with a key derived from the app's SECRET_KEY.
"""

from cryptography.fernet import Fernet
import base64
import hashlib
from app.core.config import settings


def _get_fernet_key() -> bytes:
    """
    Derive a Fernet key from the SECRET_KEY.
    Fernet keys must be 32 url-safe base64-encoded bytes.
    """
    # Use the first 32 bytes of the SHA256 hash of SECRET_KEY
    key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_password(password: str) -> str:
    """Encrypt a password string. Returns base64-encoded encrypted string."""
    if not password:
        return ""

    fernet = Fernet(_get_fernet_key())
    encrypted = fernet.encrypt(password.encode())
    return encrypted.decode()


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt an encrypted password. Returns plaintext password."""
    if not encrypted_password:
        return ""

    fernet = Fernet(_get_fernet_key())
    decrypted = fernet.decrypt(encrypted_password.encode())
    return decrypted.decode()
