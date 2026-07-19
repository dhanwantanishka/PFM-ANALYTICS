"""Authentication utilities, including secure password hashing and verification."""

import hashlib
import os

def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    # Combine salt and key and convert to hex for database storage
    return (salt + key).hex()

def verify_password(stored_hash: str, provided_password: str) -> bool:
    """Verify a password against its stored PBKDF2 hash."""
    try:
        hash_bytes = bytes.fromhex(stored_hash)
        salt = hash_bytes[:16]
        key = hash_bytes[16:]
        new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return key == new_key
    except Exception:
        return False
