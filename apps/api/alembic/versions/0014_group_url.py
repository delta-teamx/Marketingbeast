"""group_suggestions.group_url — real discovered Facebook group link

Revision ID: 0014_group_url
Revises: 0013_webhook_events
Create Date: 2026-07-08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0014_group_url"
down_revision: str | None = "0013_webhook_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "group_suggestions",
        sa.Column("group_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("group_suggestions", "group_url")
