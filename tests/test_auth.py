"""Tests for password hashing and authentication verification."""

from pfm.auth import hash_password, verify_password

def test_password_hashing() -> None:
    password = "MySecurePassword123!"
    h1 = hash_password(password)
    h2 = hash_password(password)

    # Hashes should be secure and use random salting (not identical)
    assert h1 != h2
    assert len(h1) == 96  # 16 bytes salt (32 hex characters) + 32 bytes key (64 hex characters) = 96 hex characters

    # Verification should succeed with the correct password
    assert verify_password(h1, password) is True
    assert verify_password(h2, password) is True

    # Verification should fail with wrong passwords
    assert verify_password(h1, "WrongPassword") is False
    assert verify_password(h1, "") is False
