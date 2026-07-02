"""Импорт всех моделей — чтобы Base.metadata был полным (для Alembic и тестов)."""
from app.models.group import Group, GroupMember
from app.models.token import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
)
from app.models.user import StudentProfile, TeacherProfile, User, UserRole

__all__ = [
    "User",
    "UserRole",
    "StudentProfile",
    "TeacherProfile",
    "RefreshToken",
    "EmailVerificationToken",
    "PasswordResetToken",
    "Group",
    "GroupMember",
]
