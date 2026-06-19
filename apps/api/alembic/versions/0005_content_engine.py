"""content engine: approval + hashtags + suggested_time on content_items

Revision ID: 0005_content_engine
Revises: 0004_audit
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005_content_engine"
down_revision: str | None = "0004_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "content_items",
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "content_items", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "content_items", sa.Column("hashtags", postgresql.ARRAY(sa.String()), nullable=True)
    )
    op.add_column("content_items", sa.Column("suggested_time", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("content_items", "suggested_time")
    op.drop_column("content_items", "hashtags")
    op.drop_column("content_items", "approved_at")
    op.drop_column("content_items", "approved")
