"""Модель заданий: учитель назначает ученику задачу или главу (урок)."""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BigInt, Base, TimestampMixin


class AssignmentType(str, enum.Enum):
    problem = "problem"
    lesson = "lesson"


class Assignment(Base, TimestampMixin):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[AssignmentType] = mapped_column(
        Enum(AssignmentType, name="assignment_type"), nullable=False
    )
    problem_id: Mapped[int | None] = mapped_column(
        BigInt, ForeignKey("problems.id", ondelete="CASCADE")
    )
    lesson_id: Mapped[int | None] = mapped_column(
        BigInt, ForeignKey("lessons.id", ondelete="CASCADE")
    )
    note: Mapped[str | None] = mapped_column(String(500))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
