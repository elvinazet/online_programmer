"""assignments: teacher assigns problems / lessons to students

Revision ID: 0005_assignments
Revises: 0004_exams
Create Date: 2026-07-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_assignments"
down_revision: Union[str, None] = "0004_exams"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assignments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("teacher_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.Enum("problem", "lesson", name="assignment_type"), nullable=False),
        sa.Column("problem_id", sa.BigInteger(), sa.ForeignKey("problems.id", ondelete="CASCADE")),
        sa.Column("lesson_id", sa.BigInteger(), sa.ForeignKey("lessons.id", ondelete="CASCADE")),
        sa.Column("note", sa.String(500)),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_assignments_teacher_id", "assignments", ["teacher_id"])
    op.create_index("ix_assignments_student_id", "assignments", ["student_id"])


def downgrade() -> None:
    op.drop_table("assignments")
    sa.Enum(name="assignment_type").drop(op.get_bind(), checkfirst=True)
