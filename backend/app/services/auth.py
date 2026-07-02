"""Бизнес-логика авторизации: выпуск/ротация токенов, verify/reset."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
)
from app.models.token import EmailVerificationToken, PasswordResetToken, RefreshToken
from app.models.user import User
from app.schemas.auth import TokenPair


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(dt: datetime) -> datetime:
    """Приводим к tz-aware UTC (SQLite отдаёт naive, Postgres — aware)."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def create_email_verification(db: Session, user: User) -> str:
    raw = generate_opaque_token()
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token=raw,
            expires_at=_utcnow() + timedelta(hours=settings.email_verification_ttl_hours),
        )
    )
    return raw


def create_password_reset(db: Session, user: User) -> str:
    raw = generate_opaque_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token=raw,
            expires_at=_utcnow() + timedelta(hours=settings.password_reset_ttl_hours),
        )
    )
    return raw


def issue_token_pair(db: Session, user: User) -> TokenPair:
    access = create_access_token(subject=str(user.id), role=user.role.value)
    raw_refresh = generate_opaque_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_opaque_token(raw_refresh),
            expires_at=_utcnow() + timedelta(days=settings.refresh_token_expire_days),
        )
    )
    return TokenPair(access_token=access, refresh_token=raw_refresh)


def rotate_refresh_token(db: Session, raw_refresh: str) -> TokenPair | None:
    """Проверяет refresh-токен, отзывает его и выпускает новую пару (ротация)."""
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_opaque_token(raw_refresh))
    )
    if token is None or token.revoked or _as_aware(token.expires_at) <= _utcnow():
        return None
    user = db.get(User, token.user_id)
    if user is None:
        return None
    token.revoked = True  # ротация: старый токен больше не действует
    return issue_token_pair(db, user)


def revoke_refresh_token(db: Session, raw_refresh: str) -> None:
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_opaque_token(raw_refresh))
    )
    if token is not None and not token.revoked:
        token.revoked = True


def revoke_all_refresh_tokens(db: Session, user_id: int) -> None:
    tokens = db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False)
        )
    )
    for token in tokens:
        token.revoked = True
