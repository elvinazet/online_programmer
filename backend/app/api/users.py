"""Эндпоинты профиля пользователя."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    StudentProfileUpdate,
    TeacherProfileUpdate,
    UserOut,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me/student-profile", response_model=UserOut)
def update_student_profile(
    payload: StudentProfileUpdate,
    user: User = Depends(require_role(UserRole.student)),
    db: Session = Depends(get_db),
) -> User:
    profile = user.student_profile
    if payload.avatar_url is not None:
        profile.avatar_url = payload.avatar_url
    if payload.codeforces_handle is not None:
        profile.codeforces_handle = payload.codeforces_handle
    db.commit()
    db.refresh(user)
    return user


@router.patch("/me/teacher-profile", response_model=UserOut)
def update_teacher_profile(
    payload: TeacherProfileUpdate,
    user: User = Depends(require_role(UserRole.teacher)),
    db: Session = Depends(get_db),
) -> User:
    profile = user.teacher_profile
    if payload.display_name is not None:
        profile.display_name = payload.display_name
    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.avatar_url is not None:
        profile.avatar_url = payload.avatar_url
    db.commit()
    db.refresh(user)
    return user
