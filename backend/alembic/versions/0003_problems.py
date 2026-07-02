"""problems: cf/authored problems, tags, tests, submissions, solved, cf sync

Revision ID: 0003_problems
Revises: 0002_textbooks
Create Date: 2026-07-02

Домен 3 — задачи, Codeforces, сабмиты.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_problems"
down_revision: Union[str, None] = "0002_textbooks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "problems",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.Enum("codeforces", "authored", name="problem_source"), nullable=False),
        sa.Column("cf_contest_id", sa.Integer()),
        sa.Column("cf_index", sa.String(10)),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("statement_md", sa.Text()),
        sa.Column("rating", sa.Integer()),
        sa.Column("time_limit_ms", sa.Integer(), server_default=sa.text("2000"), nullable=False),
        sa.Column("memory_limit_mb", sa.Integer(), server_default=sa.text("256"), nullable=False),
        sa.Column("url", sa.String(500)),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        *_timestamps(),
        sa.UniqueConstraint("cf_contest_id", "cf_index", name="uq_problem_cf"),
    )
    op.create_index("ix_problems_rating", "problems", ["rating"])

    op.create_table(
        "problem_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("problem_id", sa.BigInteger(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tag", sa.String(64), nullable=False),
        sa.UniqueConstraint("problem_id", "tag", name="uq_problem_tag"),
    )
    op.create_index("ix_problem_tags_problem_id", "problem_tags", ["problem_id"])
    op.create_index("ix_problem_tags_tag", "problem_tags", ["tag"])

    op.create_table(
        "problem_tests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("problem_id", sa.BigInteger(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("input", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_sample", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_index("ix_problem_tests_problem_id", "problem_tests", ["problem_id"])

    op.create_table(
        "submissions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("problem_id", sa.BigInteger(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language", sa.Enum("cpp", "python", name="submission_language"), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued", "running", "accepted", "wrong_answer", "tle", "mle",
                "runtime_error", "compile_error", name="submission_status",
            ),
            server_default=sa.text("'queued'"),
            nullable=False,
        ),
        sa.Column("passed_tests", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_tests", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("score", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("time_ms", sa.Integer()),
        sa.Column("memory_kb", sa.Integer()),
        sa.Column("compile_output", sa.Text()),
        *_timestamps(),
    )
    op.create_index("ix_submissions_student_id", "submissions", ["student_id"])
    op.create_index("ix_submissions_problem_id", "submissions", ["problem_id"])

    op.create_table(
        "student_solved_problems",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("problem_id", sa.BigInteger(), sa.ForeignKey("problems.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source", sa.Enum("cf_poll", "local", name="solved_source"), nullable=False),
        sa.Column("solved_at", sa.DateTime(timezone=True), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("student_id", "problem_id", name="uq_student_solved"),
    )
    op.create_index("ix_student_solved_student_id", "student_solved_problems", ["student_id"])
    op.create_index("ix_student_solved_problem_id", "student_solved_problems", ["problem_id"])

    op.create_table(
        "cf_sync_state",
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("last_cf_submission_id", sa.BigInteger()),
        *_timestamps(),
    )


def downgrade() -> None:
    op.drop_table("cf_sync_state")
    op.drop_table("student_solved_problems")
    op.drop_table("submissions")
    op.drop_table("problem_tests")
    op.drop_table("problem_tags")
    op.drop_table("problems")
    bind = op.get_bind()
    for enum_name in ("solved_source", "submission_status", "submission_language", "problem_source"):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
