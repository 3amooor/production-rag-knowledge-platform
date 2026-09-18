from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies.security import get_current_user
from app.db.session import get_db_session
from app.models import RefreshToken, User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserResponse,
)
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token_id,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db_session)]


def issue_token_pair(session: Session, user_id: UUID) -> TokenPairResponse:
    refresh_token, token_id, expires_at = create_refresh_token(user_id)
    session.add(
        RefreshToken(user_id=user_id, token_hash=hash_token_id(token_id), expires_at=expires_at)
    )
    return TokenPairResponse(access_token=create_access_token(user_id), refresh_token=refresh_token)


@router.post("/register", response_model=TokenPairResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: DbSession) -> TokenPairResponse:
    user = User(email=str(payload.email).lower(), password_hash=hash_password(payload.password))
    session.add(user)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="An account with this email already exists."
        ) from None
    tokens = issue_token_pair(session, user.id)
    session.commit()
    return tokens


@router.post("/login", response_model=TokenPairResponse)
def login(payload: LoginRequest, session: DbSession) -> TokenPairResponse:
    user = session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    tokens = issue_token_pair(session, user.id)
    session.commit()
    return tokens


@router.post("/refresh", response_model=TokenPairResponse)
def refresh(payload: RefreshRequest, session: DbSession) -> TokenPairResponse:
    try:
        claims = decode_token(payload.refresh_token, "refresh")
        user_id = UUID(claims["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid refresh token.") from None
    stored = session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token_id(claims["jti"]))
    )
    if (
        stored is None
        or stored.user_id != user_id
        or stored.revoked_at
        or stored.expires_at <= datetime.now(UTC)
    ):
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    stored.revoked_at = datetime.now(UTC)
    tokens = issue_token_pair(session, user_id)
    session.commit()
    return tokens


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
