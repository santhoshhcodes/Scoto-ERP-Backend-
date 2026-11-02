"""
Core Security Module
Exposes password verification, hashing, and JWT token handling.
"""

from src.utils.security import (
    ALGORITHM,
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    get_password_hash,
    pwd_context,
    verify_legacy_password,
    verify_password,
)

__all__ = [
    "ALGORITHM",
    "DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES",
    "create_access_token",
    "decode_access_token",
    "get_password_hash",
    "pwd_context",
    "verify_legacy_password",
    "verify_password",
]
