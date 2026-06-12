"""ads: ad_accounts, ad_campaigns, ad_creatives

Revision ID: 0009_ads
Revises: 0008_inbox
Create Date: 2026-06-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0009_ads"
down_revision: str | None = "0008_inbox"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    campaign_status = postgresql.ENUM(
        "draft", "active", "paused", name="campaign_status", create_type=False
    )
    creative_status = postgresql.ENUM(
        "active", "paused", name="creative_status", create_type=False
    )
    campaign_status.create(op.get_bind(), checkfirst=True)
    creative_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ad_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(200), nullable=False),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="connected"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ad_accounts_brand_id", "ad_accounts", ["brand_id"])

    op.create_table(
        "ad_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ad_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ad_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(200), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("objective", sa.String(50), nullable=False, server_default="LEADS"),
        sa.Column("status", campaign_status, nullable=False, server_default="active"),
        sa.Column("daily_budget", sa.Float(), nullable=False, server_default="10"),
        sa.Column("metrics_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ad_campaigns_brand_id", "ad_campaigns", ["brand_id"])
    op.create_index("ix_ad_campaigns_status", "ad_campaigns", ["status"])

    op.create_table(
        "ad_creatives",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "campaign_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ad_campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(200), nullable=True),
        sa.Column("variation_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("headline", sa.String(255), nullable=False),
        sa.Column("primary_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", creative_status, nullable=False, server_default="active"),
        sa.Column("metrics_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_ad_creatives_campaign_id", "ad_creatives", ["campaign_id"])


def downgrade() -> None:
    op.drop_table("ad_creatives")
    op.drop_table("ad_campaigns")
    op.drop_table("ad_accounts")
    op.execute("DROP TYPE IF EXISTS creative_status")
    op.execute("DROP TYPE IF EXISTS campaign_status")
