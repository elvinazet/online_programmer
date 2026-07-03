"""Модели сабмитов (локальный judge), решённых задач и курсора опроса CF."""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import BigInt, Base, TimestampMixin


class SubmissionLanguage(str, enum.Enum):
    cpp = "cpp"
    python = "python"


class SubmissionStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    accepted = "accepted"
    wrong_answer = "wrong_answer"
    tle = "tle"
    mle = "mle"
    runtime_error = "runtime_error"
    compile_error = "compile_error"


class SolvedSource(str, enum.Enum):
    cf_poll = "cf_poll"
    local = "local"


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    problem_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("problems.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # практический сабмит в рамках попытки экзамена (без DB-FK — связь на уровне app)
    exam_attempt_id: Mapped[int | None] = mapped_column(BigInt, index=True)
    language: Mapped[SubmissionLanguage] = mapped_column(
        Enum(SubmissionLanguage, name="submission_language"), nullable=False
    )
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status"),
        default=SubmissionStatus.queued,
        nullable=False,
    )
    passed_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    time_ms: Mapped[int | None] = mapped_column(Integer)
    memory_kb: Mapped[int | None] = mapped_column(Integer)
    compile_output: Mapped[str | None] = mapped_column(Text)


class StudentSolvedProblem(Base, TimestampMixin):
    __tablename__ = "student_solved_problems"
    __table_args__ = (
        UniqueConstraint("student_id", "problem_id", name="uq_student_solved"),
    )

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    problem_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("problems.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source: Mapped[SolvedSource] = mapped_column(
        Enum(SolvedSource, name="solved_source"), nullable=False
    )
    solved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CfSyncState(Base, TimestampMixin):
    __tablename__ = "cf_sync_state"

    student_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_cf_submission_id: Mapped[int | None] = mapped_column(BigInt)
