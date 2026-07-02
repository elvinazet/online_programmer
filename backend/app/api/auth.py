"""Эндпоинты авторизации."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.core.utils import normalize_email
from app.db.session import get_db
from app.models.token import EmailVerificationToken, PasswordResetToken
from app.models.user import StudentProfile, TeacherProfile, User, UserRole
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenPair,
    VerifyEmailRequest,
)
from app.services import auth as auth_service
from app.services.auth import _as_aware, _utcnow
from app.services.email import send_password_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> MessageResponse:
    email = normalize_email(payload.email)
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email уже зарегистрирован")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        email_verified=False,
    )
    db.add(user)
    db.flush()  # получаем user.id

    if payload.role == UserRole.student:
        db.add(StudentProfile(user_id=user.id, codeforces_handle=payload.codeforces_handle))
    else:
        db.add(TeacherProfile(user_id=user.id, display_name=payload.display_name))

    raw_token = auth_service.create_email_verification(db, user)
    db.commit()

    send_verification_email(email, raw_token)
    return MessageResponse(message="Регистрация успешна. Проверьте email для подтверждения.")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)) -> MessageResponse:
    token = db.scalar(
        select(EmailVerificationToken).where(EmailVerificationToken.token == payload.token)
    )
    if token is None or token.used or _as_aware(token.expires_at) <= _utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Недействительный или истёкший токен")

    user = db.get(User, token.user_id)
    user.email_verified = True
    token.used = True
    db.commit()
    return MessageResponse(message="Email подтверждён. Теперь можно войти.")


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    email = normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный email или пароль")
    if not user.email_verified:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Email не подтверждён")

    pair = auth_service.issue_token_pair(db, user)
    db.commit()
    return pair


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    pair = auth_service.rotate_refresh_token(db, payload.refresh_token)
    if pair is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Недействительный refresh-токен")
    db.commit()
    return pair


@router.post("/logout", response_model=MessageResponse)
def logout(payload: RefreshRequest, db: Session = Depends(get_db)) -> MessageResponse:
    auth_service.revoke_refresh_token(db, payload.refresh_token)
    db.commit()
    return MessageResponse(message="Выход выполнен")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    email = normalize_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        raw_token = auth_service.create_password_reset(db, user)
        db.commit()
        send_password_reset_email(email, raw_token)
    # Ответ одинаков независимо от существования аккаунта (не раскрываем базу).
    return MessageResponse(message="Если аккаунт существует, письмо для сброса отправлено.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    token = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token == payload.token)
    )
    if token is None or token.used or _as_aware(token.expires_at) <= _utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Недействительный или истёкший токен")

    user = db.get(User, token.user_id)
    user.password_hash = hash_password(payload.new_password)
    token.used = True
    auth_service.revoke_all_refresh_tokens(db, user.id)  # разлогиниваем все сессии
    db.commit()
    return MessageResponse(message="Пароль обновлён. Войдите с новым паролем.")
