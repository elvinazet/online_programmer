"""textbooks: courses, levels, modules, lessons, questions, progress

Revision ID: 0002_textbooks
Revises: 0001_initial
Create Date: 2026-07-02

Домен 2 — учебники и прогресс.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_textbooks"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# JSONB в Postgres, обычный JSON в SQLite.
_JSON = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("language", sa.Enum("cpp", "python", name="course_language"), nullable=False),
        sa.Column("description", sa.Text()),
        *_timestamps(),
    )

    op.create_table(
        "levels",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "course_id", sa.BigInteger(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "name",
            sa.Enum("beginner", "intermediate", "advanced", name="level_name"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_levels_course_id", "levels", ["course_id"])

    op.create_table(
        "modules",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "level_id", sa.BigInteger(), sa.ForeignKey("levels.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_modules_level_id", "modules", ["level_id"])

    op.create_table(
        "lessons",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "module_id", sa.BigInteger(), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content_md", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        *_timestamps(),
    )
    op.create_index("ix_lessons_module_id", "lessons", ["module_id"])

    op.create_table(
        "questions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "module_id", sa.BigInteger(), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "type",
            sa.Enum(
                "single_choice",
                "multiple_choice",
                "short_answer",
                "code_output",
                name="question_type",
            ),
            nullable=False,
        ),
        sa.Column("prompt_md", sa.Text(), nullable=False),
        sa.Column("options", _JSON),
        sa.Column("correct_answer", _JSON, nullable=False),
        sa.Column("explanation_md", sa.Text()),
        sa.Column("difficulty", sa.Integer()),
        *_timestamps(),
    )
    op.create_index("ix_questions_module_id", "questions", ["module_id"])

    op.create_table(
        "lesson_questions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "lesson_id", sa.BigInteger(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "question_id",
            sa.BigInteger(),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("lesson_id", "question_id", name="uq_lesson_question"),
    )
    op.create_index("ix_lesson_questions_lesson_id", "lesson_questions", ["lesson_id"])

    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "lesson_id", sa.BigInteger(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "status",
            sa.Enum("not_started", "in_progress", "completed", name="progress_status"),
            server_default=sa.text("'not_started'"),
            nullable=False,
        ),
        sa.Column("quiz_score", sa.Integer()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        *_timestamps(),
        sa.UniqueConstraint("student_id", "lesson_id", name="uq_lesson_progress"),
    )
    op.create_index("ix_lesson_progress_student_id", "lesson_progress", ["student_id"])
    op.create_index("ix_lesson_progress_lesson_id", "lesson_progress", ["lesson_id"])


def downgrade() -> None:
    op.drop_table("lesson_progress")
    op.drop_table("lesson_questions")
    op.drop_table("questions")
    op.drop_table("lessons")
    op.drop_table("modules")
    op.drop_table("levels")
    op.drop_table("courses")
    bind = op.get_bind()
    for enum_name in ("progress_status", "question_type", "level_name", "course_language"):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
