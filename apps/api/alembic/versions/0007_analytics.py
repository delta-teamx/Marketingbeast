"""analytics: metric_snapshots, reports, competitors

Revision ID: 0007_analytics
Revises: 0006_onboarding
Create Date: 2026-06-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007_analytics"
down_revision: str | None = "0006_onboarding"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    report_period = postgresql.ENUM("weekly", "monthly", name="report_period", create_type=False)
    report_period.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "metric_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "social_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("social_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("followers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("engagement", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("posts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("social_account_id", "snapshot_date", name="uq_snapshot_account_day"),
    )
    op.create_index("ix_metric_snapshots_brand_id", "metric_snapshots", ["brand_id"])
    op.create_index("ix_metric_snapshots_snapshot_date", "metric_snapshots", ["snapshot_date"])

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period", report_period, nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("metrics_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reports_brand_id", "reports", ["brand_id"])

    op.create_table(
        "competitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("handle", sa.String(200), nullable=True),
        sa.Column("platform", sa.String(50), nullable=True),
        sa.Column("followers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("posting_frequency", sa.String(50), nullable=True),
        sa.Column("engagement_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_competitors_brand_id", "competitors", ["brand_id"])


def downgrade() -> None:
    op.drop_table("competitors")
    op.drop_table("reports")
    op.drop_table("metric_snapshots")
    op.execute("DROP TYPE IF EXISTS report_period")
