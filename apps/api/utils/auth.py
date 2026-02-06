from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _ensure_bcrypt_limit(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password too long (max 72 bytes for bcrypt).")
    return password


def hash_password(password: str) -> str:
    password = _ensure_bcrypt_limit(password)
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    password = _ensure_bcrypt_limit(password)
    return pwd_context.verify(password, hashed)


def create_access_token(subject: str, tenant_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_exp_minutes)
    payload = {"sub": subject, "tenant_id": tenant_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except Exception:
        return None
