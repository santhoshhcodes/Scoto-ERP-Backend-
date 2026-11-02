"""
Security and cryptographic utility functions.
Handles JWT token creation and verification, password hashing with bcrypt,
and legacy password verification for backwards compatibility.
"""

import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings

# Password hashing context (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12  # 12 hours


def verify_legacy_password(
    plain_password: str,
    stored_password: str,
) -> bool:
    """
    Verify legacy Base64-encoded or plain-text passwords.
    Plain-text support is retained for compatibility with the existing legacy database.
    """
    if not plain_password or not stored_password:
        return False
    try:
        encoded = base64.b64encode(
            plain_password.encode("utf-8")
        ).decode("utf-8")

        return (
            encoded == stored_password
            or plain_password == stored_password
        )
    except (TypeError, UnicodeError):
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a modern bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Fallback to legacy check if stored password is not bcrypt format
        return verify_legacy_password(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        return None
