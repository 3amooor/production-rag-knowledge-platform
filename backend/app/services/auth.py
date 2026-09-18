import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hasher = PasswordHash.recommended()
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def _encode_token(subject: UUID, token_type: str, expires_at: datetime, token_id: UUID) -> str:
    return jwt.encode(
        {"sub": str(subject), "type": token_type, "exp": expires_at, "jti": str(token_id)},
        get_settings().jwt_secret_key,
        algorithm=JWT_ALGORITHM,
    )


def create_access_token(user_id: UUID) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=get_settings().jwt_access_token_minutes)
    return _encode_token(user_id, "access", expires_at, uuid4())


def create_refresh_token(user_id: UUID) -> tuple[str, UUID, datetime]:
    token_id = uuid4()
    expires_at = datetime.now(UTC) + timedelta(days=get_settings().jwt_refresh_token_days)
    return _encode_token(user_id, "refresh", expires_at, token_id), token_id, expires_at


def decode_token(token: str, expected_type: str) -> dict[str, str]:
    payload = jwt.decode(token, get_settings().jwt_secret_key, algorithms=[JWT_ALGORITHM])
    if payload.get("type") != expected_type or not payload.get("sub") or not payload.get("jti"):
        raise jwt.InvalidTokenError("Invalid token type or claims.")
    return payload


def hash_token_id(token_id: str | UUID) -> str:
    return hashlib.sha256(str(token_id).encode()).hexdigest()
