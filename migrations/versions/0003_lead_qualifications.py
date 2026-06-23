"""lead qualifications (BANT)

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lead_qualifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("lead_id", sa.Uuid(), nullable=True),
        sa.Column("budget", sa.String(length=16), nullable=False),
        sa.Column("authority", sa.String(length=16), nullable=False),
        sa.Column("need", sa.String(length=16), nullable=False),
        sa.Column("timeline", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=16), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_lead_qualifications_conversation_id",
        "lead_qualifications",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_lead_qualifications_conversation_id", table_name="lead_qualifications")
    op.drop_table("lead_qualifications")
