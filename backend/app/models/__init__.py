"""Импорт всех моделей — чтобы Base.metadata был полным (для Alembic и тестов)."""
from app.models.content import Course, CourseLanguage, Lesson, Level, LevelName, Module
from app.models.group import Group, GroupMember
from app.models.quiz import (
    LessonProgress,
    LessonQuestion,
    ProgressStatus,
    Question,
    QuestionType,
)
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
    "Course",
    "CourseLanguage",
    "Level",
    "LevelName",
    "Module",
    "Lesson",
    "Question",
    "QuestionType",
    "LessonQuestion",
    "LessonProgress",
    "ProgressStatus",
]
