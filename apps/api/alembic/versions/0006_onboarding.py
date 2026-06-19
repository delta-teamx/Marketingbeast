"""onboarding: onboarding_profiles table

Revision ID: 0006_onboarding
Revises: 0005_content_engine
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006_onboarding"
down_revision: str | None = "0005_content_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "onboarding_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("goal", sa.String(100), nullable=True),
        sa.Column("platforms", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("posting_frequency", sa.String(50), nullable=True),
        sa.Column("monthly_budget", sa.String(50), nullable=True),
        sa.Column("biggest_challenge", sa.Text(), nullable=True),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_onboarding_profiles_brand_id", "onboarding_profiles", ["brand_id"])


def downgrade() -> None:
    op.drop_table("onboarding_profiles")
