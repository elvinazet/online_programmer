"""Схемы профиля и вывода пользователя."""
from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class StudentProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    avatar_url: str | None = None
    codeforces_handle: str | None = None
    streak_count: int = 0


class TeacherProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: UserRole
    email_verified: bool
    student_profile: StudentProfileOut | None = None
    teacher_profile: TeacherProfileOut | None = None


class StudentProfileUpdate(BaseModel):
    avatar_url: str | None = None
    codeforces_handle: str | None = None


class TeacherProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
