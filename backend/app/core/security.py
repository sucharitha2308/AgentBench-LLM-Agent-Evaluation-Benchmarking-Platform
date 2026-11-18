import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from app.config import settings

# Argon2 password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def _get_fernet_key(secret: str) -> bytes:
    """Derive a URL-safe 32-byte Fernet key from the configured encryption key."""
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest)

_fernet = Fernet(_get_fernet_key(settings.ENCRYPTION_KEY))


def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against an Argon2 hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None
) -> str:
    """Generate a JWT access token with user ID subject."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access"
    }
    if extra_claims:
        to_encode.update(extra_claims)
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, Any]) -> str:
    """Generate a JWT refresh token with longer TTL."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return {}


def encrypt_secret(raw_secret: str) -> str:
    """Encrypt an API key or sensitive token at rest."""
    if not raw_secret:
        return ""
    return _fernet.encrypt(raw_secret.encode()).decode()


def decrypt_secret(encrypted_secret: str) -> str:
    """Decrypt an encrypted secret."""
    if not encrypted_secret:
        return ""
    try:
        return _fernet.decrypt(encrypted_secret.encode()).decode()
    except Exception:
        return ""
