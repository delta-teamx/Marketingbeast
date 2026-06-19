"""flagship audit: audit_reports table

Revision ID: 0004_audit
Revises: 0003_group_finder
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_audit"
down_revision: str | None = "0003_group_finder"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("overall_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overall_grade", sa.String(2), nullable=False, server_default="F"),
        sa.Column("sections", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("findings", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("recommendations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("strategy_brief", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_plan", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_reports_brand_id", "audit_reports", ["brand_id"])


def downgrade() -> None:
    op.drop_table("audit_reports")
