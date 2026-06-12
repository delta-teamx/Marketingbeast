"""ai media: org credits, media_jobs, media_assets, credit_ledger

Revision ID: 0010_media
Revises: 0009_ads
Create Date: 2026-06-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0010_media"
down_revision: str | None = "0009_ads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("credit_balance", sa.Integer(), nullable=False, server_default="0"),
    )

    job_status = postgresql.ENUM(
        "queued", "rendering", "ready", "failed", name="media_job_status", create_type=False
    )
    job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "media_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="queued"),
        sa.Column("prompt", sa.Text(), nullable=False, server_default=""),
        sa.Column("script", sa.Text(), nullable=False, server_default=""),
        sa.Column("storyboard_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("external_job_id", sa.String(200), nullable=True),
        sa.Column("asset_url", sa.String(500), nullable=True),
        sa.Column("cost_credits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_media_jobs_brand_id", "media_jobs", ["brand_id"])
    op.create_index("ix_media_jobs_status", "media_jobs", ["status"])

    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(20), nullable=False, server_default="video"),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="ai_generated"),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column(
            "media_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("media_jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_media_assets_brand_id", "media_assets", ["brand_id"])

    op.create_table(
        "credit_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_credit_ledger_org_id", "credit_ledger", ["org_id"])


def downgrade() -> None:
    op.drop_table("credit_ledger")
    op.drop_table("media_assets")
    op.drop_table("media_jobs")
    op.execute("DROP TYPE IF EXISTS media_job_status")
    op.drop_column("organizations", "credit_balance")
