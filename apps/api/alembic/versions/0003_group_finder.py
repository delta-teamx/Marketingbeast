"""group lead finder: brand niche fields + group_suggestions + group_post_tasks

Revision ID: 0003_group_finder
Revises: 0002_content
Create Date: 2026-06-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_group_finder"
down_revision: str | None = "0002_content"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("brands", sa.Column("niche_summary", sa.String(1000), nullable=True))
    op.add_column(
        "brands", sa.Column("niche_keywords", postgresql.ARRAY(sa.String()), nullable=True)
    )

    suggestion_status = postgresql.ENUM(
        "suggested", "tracked", "dismissed",
        name="group_suggestion_status", create_type=False,
    )
    task_status = postgresql.ENUM(
        "queued", "claimed", "posted", "skipped",
        name="group_task_status", create_type=False,
    )
    suggestion_status.create(op.get_bind(), checkfirst=True)
    task_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "group_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("search_keyword", sa.String(300), nullable=False),
        sa.Column("estimated_size", sa.String(50), nullable=True),
        sa.Column("relevance_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lead_quality_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("suggested_post_angle", sa.Text(), nullable=True),
        sa.Column("status", suggestion_status, nullable=False, server_default="suggested"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_group_suggestions_brand_id", "group_suggestions", ["brand_id"])
    op.create_index("ix_group_suggestions_status", "group_suggestions", ["status"])

    op.create_table(
        "group_post_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "brand_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("brands.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "group_suggestion_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("group_suggestions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False, server_default=""),
        sa.Column("media_urls", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("status", task_status, nullable=False, server_default="queued"),
        sa.Column("external_ref", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_group_post_tasks_brand_id", "group_post_tasks", ["brand_id"])
    op.create_index("ix_group_post_tasks_status", "group_post_tasks", ["status"])


def downgrade() -> None:
    op.drop_table("group_post_tasks")
    op.drop_table("group_suggestions")
    op.execute("DROP TYPE IF EXISTS group_task_status")
    op.execute("DROP TYPE IF EXISTS group_suggestion_status")
    op.drop_column("brands", "niche_keywords")
    op.drop_column("brands", "niche_summary")
