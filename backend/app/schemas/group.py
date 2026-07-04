"""Схемы групп."""
from pydantic import BaseModel, ConfigDict, EmailStr


class GroupCreate(BaseModel):
    name: str


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    teacher_id: int


class AddMemberRequest(BaseModel):
    student_email: EmailStr


class GroupMemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: int
    email: EmailStr


class GroupProgressItem(BaseModel):
    student_id: int
    email: EmailStr
    solved_total: int
    lessons_completed: int
    exams_passed: int
