"""Модели банка вопросов, состава мини-квиза урока и прогресса ученика."""
import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BigInt, Base, JsonB, TimestampMixin


class QuestionType(str, enum.Enum):
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    short_answer = "short_answer"
    code_output = "code_output"


class ProgressStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"


class Question(Base, TimestampMixin):
    """Вопрос банка темы (модуля). Используется мини-квизами и экзаменами."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("modules.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"), nullable=False
    )
    prompt_md: Mapped[str] = mapped_column(Text, nullable=False)
    # варианты ответа (для choice-типов); список строк
    options: Mapped[list | None] = mapped_column(JsonB)
    # эталон: {"correct": idx} | {"correct": [idx,...]} | {"accepted": [str,...]}
    correct_answer: Mapped[dict] = mapped_column(JsonB, nullable=False)
    explanation_md: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[int | None] = mapped_column(Integer)


class LessonQuestion(Base, TimestampMixin):
    """Состав мини-квиза урока (какие вопросы и в каком порядке)."""

    __tablename__ = "lesson_questions"
    __table_args__ = (
        UniqueConstraint("lesson_id", "question_id", name="uq_lesson_question"),
    )

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    lesson_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question: Mapped["Question"] = relationship()


class LessonProgress(Base, TimestampMixin):
    """Прогресс ученика по уроку."""

    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id", name="uq_lesson_progress"),
    )

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lesson_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[ProgressStatus] = mapped_column(
        Enum(ProgressStatus, name="progress_status"),
        default=ProgressStatus.not_started,
        nullable=False,
    )
    quiz_score: Mapped[int | None] = mapped_column(Integer)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
