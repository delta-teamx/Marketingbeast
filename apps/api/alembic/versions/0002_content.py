"""content publishing: content_items + content_targets, social_account columns

Revision ID: 0002_content
Revises: 0001_initial
Create Date: 2026-06-09
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_content"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("social_accounts", sa.Column("display_name", sa.String(200), nullable=True))
    op.add_column("social_accounts", sa.Column("ig_user_id", sa.String(200), nullable=True))

    content_type = postgresql.ENUM(
        "post", "reel", "story", name="content_type", create_type=False
    )
    content_status = postgresql.ENUM(
        "draft", "scheduled", "publishing", "published", "failed",
        name="content_status", create_type=False,
    )
    target_status = postgresql.ENUM(
        "pending", "published", "failed", name="target_status", create_type=False
    )
    content_type.create(op.get_bind(), checkfirst=True)
    content_status.create(op.get_bind(), checkfirst=True)
    target_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "content_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content_type", content_type, nullable=False, server_default="post"),
        sa.Column("status", content_status, nullable=False, server_default="draft"),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("media_urls", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("scheduled_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_content_items_brand_id", "content_items", ["brand_id"])
    op.create_index("ix_content_items_status", "content_items", ["status"])
    op.create_index("ix_content_items_scheduled_time", "content_items", ["scheduled_time"])

    op.create_table(
        "content_targets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "content_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("content_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "social_account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("social_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", target_status, nullable=False, server_default="pending"),
        sa.Column("external_post_id", sa.String(255), nullable=True),
        sa.Column("permalink", sa.String(500), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_content_targets_content_item_id", "content_targets", ["content_item_id"])


def downgrade() -> None:
    op.drop_table("content_targets")
    op.drop_table("content_items")
    op.execute("DROP TYPE IF EXISTS target_status")
    op.execute("DROP TYPE IF EXISTS content_status")
    op.execute("DROP TYPE IF EXISTS content_type")
    op.drop_column("social_accounts", "ig_user_id")
    op.drop_column("social_accounts", "display_name")
