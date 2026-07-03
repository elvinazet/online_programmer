"""Модели экзаменов: конфигурация, попытки, материализованный вариант, события."""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BigInt, Base, JsonB, TimestampMixin


class AttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    timed_out = "timed_out"


class AttemptEventType(str, enum.Enum):
    focus_lost = "focus_lost"
    focus_gained = "focus_gained"


class Exam(Base, TimestampMixin):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    level_from_id: Mapped[int | None] = mapped_column(
        BigInt, ForeignKey("levels.id", ondelete="SET NULL")
    )
    target_level_id: Mapped[int | None] = mapped_column(
        BigInt, ForeignKey("levels.id", ondelete="SET NULL")
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=7200, nullable=False)
    pass_threshold: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    retake_delay_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    practical_weight: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    theory_weight: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="SET NULL")
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    practical_problems: Mapped[list["ExamPracticalProblem"]] = relationship(
        back_populates="exam", order_by="ExamPracticalProblem.order_index",
        cascade="all, delete-orphan",
    )
    theory_configs: Mapped[list["ExamTheoryConfig"]] = relationship(
        back_populates="exam", cascade="all, delete-orphan"
    )


class ExamPracticalProblem(Base):
    __tablename__ = "exam_practical_problems"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("exams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    problem_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    exam: Mapped["Exam"] = relationship(back_populates="practical_problems")


class ExamTheoryConfig(Base):
    __tablename__ = "exam_theory_config"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("exams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    module_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
    )
    num_questions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    exam: Mapped["Exam"] = relationship(back_populates="theory_configs")


class ExamAttempt(Base, TimestampMixin):
    __tablename__ = "exam_attempts"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("exams.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus, name="attempt_status"),
        default=AttemptStatus.in_progress,
        nullable=False,
    )
    practical_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    theory_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    next_retake_allowed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    problems: Mapped[list["AttemptProblem"]] = relationship(
        order_by="AttemptProblem.order_index", cascade="all, delete-orphan"
    )
    questions: Mapped[list["AttemptQuestion"]] = relationship(
        order_by="AttemptQuestion.order_index", cascade="all, delete-orphan"
    )


class AttemptProblem(Base):
    __tablename__ = "attempt_problems"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("exam_attempts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    problem_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)


class AttemptQuestion(Base):
    __tablename__ = "attempt_questions"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("exam_attempts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # перестановка индексов вариантов (антивариативность); None для текстовых
    options_order: Mapped[list | None] = mapped_column(JsonB)
    student_answer: Mapped[object | None] = mapped_column(JsonB)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class AttemptEvent(Base, TimestampMixin):
    __tablename__ = "attempt_events"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("exam_attempts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[AttemptEventType] = mapped_column(
        Enum(AttemptEventType, name="attempt_event_type"), nullable=False
    )


class StudentLevelAccess(Base, TimestampMixin):
    __tablename__ = "student_level_access"
    __table_args__ = (
        UniqueConstraint("student_id", "level_id", name="uq_student_level_access"),
    )

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    level_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("levels.id", ondelete="CASCADE"), index=True, nullable=False
    )
    unlocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exam_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
