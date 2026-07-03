"""exams: config, attempts, materialized variant, events, level access

Revision ID: 0004_exams
Revises: 0003_problems
Create Date: 2026-07-02

Домен 4 — экзамены, разбор, доступ к уровням.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_exams"
down_revision: Union[str, None] = "0003_problems"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_JSON = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "exams",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("level_from_id", sa.BigInteger(), sa.ForeignKey("levels.id", ondelete="SET NULL")),
        sa.Column("target_level_id", sa.BigInteger(), sa.ForeignKey("levels.id", ondelete="SET NULL")),
        sa.Column("duration_seconds", sa.Integer(), server_default=sa.text("7200"), nullable=False),
        sa.Column("pass_threshold", sa.Float(), server_default=sa.text("0.7"), nullable=False),
        sa.Column("retake_delay_days", sa.Integer(), server_default=sa.text("3"), nullable=False),
        sa.Column("practical_weight", sa.Float(), server_default=sa.text("0.5"), nullable=False),
        sa.Column("theory_weight", sa.Float(), server_default=sa.text("0.5"), nullable=False),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("is_published", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_timestamps(),
    )

    op.create_table(
        "exam_practical_problems",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("exam_id", sa.BigInteger(), sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("problem_id", sa.BigInteger(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("max_score", sa.Integer(), server_default=sa.text("100"), nullable=False),
    )
    op.create_index("ix_exam_practical_problems_exam_id", "exam_practical_problems", ["exam_id"])

    op.create_table(
        "exam_theory_config",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("exam_id", sa.BigInteger(), sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.BigInteger(), sa.ForeignKey("modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("num_questions", sa.Integer(), server_default=sa.text("5"), nullable=False),
    )
    op.create_index("ix_exam_theory_config_exam_id", "exam_theory_config", ["exam_id"])

    op.create_table(
        "exam_attempts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("exam_id", sa.BigInteger(), sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column(
            "status",
            sa.Enum("in_progress", "submitted", "timed_out", name="attempt_status"),
            server_default=sa.text("'in_progress'"),
            nullable=False,
        ),
        sa.Column("practical_score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("theory_score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("next_retake_allowed_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index("ix_exam_attempts_exam_id", "exam_attempts", ["exam_id"])
    op.create_index("ix_exam_attempts_student_id", "exam_attempts", ["student_id"])

    op.create_table(
        "attempt_problems",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("attempt_id", sa.BigInteger(), sa.ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("problem_id", sa.BigInteger(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("max_score", sa.Integer(), server_default=sa.text("100"), nullable=False),
    )
    op.create_index("ix_attempt_problems_attempt_id", "attempt_problems", ["attempt_id"])

    op.create_table(
        "attempt_questions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("attempt_id", sa.BigInteger(), sa.ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", sa.BigInteger(), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("options_order", _JSON),
        sa.Column("student_answer", _JSON),
        sa.Column("is_correct", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("score", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_index("ix_attempt_questions_attempt_id", "attempt_questions", ["attempt_id"])

    op.create_table(
        "attempt_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("attempt_id", sa.BigInteger(), sa.ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "type",
            sa.Enum("focus_lost", "focus_gained", name="attempt_event_type"),
            nullable=False,
        ),
        *_timestamps(),
    )
    op.create_index("ix_attempt_events_attempt_id", "attempt_events", ["attempt_id"])

    op.create_table(
        "student_level_access",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level_id", sa.BigInteger(), sa.ForeignKey("levels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unlocked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("exam_passed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("student_id", "level_id", name="uq_student_level_access"),
    )
    op.create_index("ix_student_level_access_student_id", "student_level_access", ["student_id"])
    op.create_index("ix_student_level_access_level_id", "student_level_access", ["level_id"])

    # связь практического сабмита с попыткой экзамена
    op.add_column("submissions", sa.Column("exam_attempt_id", sa.BigInteger()))
    op.create_index("ix_submissions_exam_attempt_id", "submissions", ["exam_attempt_id"])


def downgrade() -> None:
    op.drop_index("ix_submissions_exam_attempt_id", table_name="submissions")
    op.drop_column("submissions", "exam_attempt_id")
    op.drop_table("student_level_access")
    op.drop_table("attempt_events")
    op.drop_table("attempt_questions")
    op.drop_table("attempt_problems")
    op.drop_table("exam_attempts")
    op.drop_table("exam_theory_config")
    op.drop_table("exam_practical_problems")
    op.drop_table("exams")
    bind = op.get_bind()
    for enum_name in ("attempt_event_type", "attempt_status"):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
