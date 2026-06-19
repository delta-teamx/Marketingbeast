"""processed webhook events (idempotency ledger)

Revision ID: 0013_webhook_events
Revises: 0012_billing
Create Date: 2026-06-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0013_webhook_events"
down_revision: str | None = "0012_billing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "processed_webhook_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("event_id", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False, server_default="stripe"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_processed_webhook_events_event_id",
        "processed_webhook_events",
        ["event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_processed_webhook_events_event_id", table_name="processed_webhook_events"
    )
    op.drop_table("processed_webhook_events")
