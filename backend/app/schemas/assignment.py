"""Схемы заданий."""
from datetime import datetime

from pydantic import BaseModel, model_validator

from app.models.assignment import AssignmentType


class AssignmentCreate(BaseModel):
    type: AssignmentType
    student_id: int | None = None
    group_id: int | None = None
    problem_id: int | None = None
    lesson_id: int | None = None
    note: str | None = None
    due_date: datetime | None = None

    @model_validator(mode="after")
    def _check(self):
        if not self.student_id and not self.group_id:
            raise ValueError("нужен student_id или group_id")
        if self.type == AssignmentType.problem and not self.problem_id:
            raise ValueError("для задачи нужен problem_id")
        if self.type == AssignmentType.lesson and not self.lesson_id:
            raise ValueError("для главы нужен lesson_id")
        return self


class AssignmentOut(BaseModel):
    id: int
    type: AssignmentType
    title: str
    problem_id: int | None = None
    lesson_id: int | None = None
    note: str | None = None
    due_date: datetime | None = None
    done: bool = False
