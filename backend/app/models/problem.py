"""Модели задач: кэш Codeforces и авторские задачи, теги, тесты."""
import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BigInt, Base, TimestampMixin


class ProblemSource(str, enum.Enum):
    codeforces = "codeforces"
    authored = "authored"


class Problem(Base, TimestampMixin):
    __tablename__ = "problems"
    __table_args__ = (
        UniqueConstraint("cf_contest_id", "cf_index", name="uq_problem_cf"),
    )

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    source: Mapped[ProblemSource] = mapped_column(
        Enum(ProblemSource, name="problem_source"), nullable=False
    )
    cf_contest_id: Mapped[int | None] = mapped_column(Integer)
    cf_index: Mapped[str | None] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    statement_md: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[int | None] = mapped_column(Integer, index=True)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256, nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    created_by: Mapped[int | None] = mapped_column(
        BigInt, ForeignKey("users.id", ondelete="SET NULL")
    )

    tags: Mapped[list["ProblemTag"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan"
    )
    tests: Mapped[list["ProblemTest"]] = relationship(
        back_populates="problem", order_by="ProblemTest.order_index", cascade="all, delete-orphan"
    )


class ProblemTag(Base):
    __tablename__ = "problem_tags"
    __table_args__ = (UniqueConstraint("problem_id", "tag", name="uq_problem_tag"),)

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("problems.id", ondelete="CASCADE"), index=True, nullable=False
    )
    tag: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    problem: Mapped["Problem"] = relationship(back_populates="tags")


class ProblemTest(Base):
    __tablename__ = "problem_tests"

    id: Mapped[int] = mapped_column(BigInt, primary_key=True, autoincrement=True)
    problem_id: Mapped[int] = mapped_column(
        BigInt, ForeignKey("problems.id", ondelete="CASCADE"), index=True, nullable=False
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    problem: Mapped["Problem"] = relationship(back_populates="tests")
