"""agency: org plan, membership email, org_invites

Revision ID: 0011_agency
Revises: 0010_media
Create Date: 2026-06-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0011_agency"
down_revision: str | None = "0010_media"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "organizations",
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
    )
    op.add_column("memberships", sa.Column("email", sa.String(320), nullable=True))

    invite_status = postgresql.ENUM(
        "pending", "accepted", "revoked", name="invite_status", create_type=False
    )
    invite_status.create(op.get_bind(), checkfirst=True)
    # org_role already exists (from 0001); reference without creating.
    org_role = postgresql.ENUM(name="org_role", create_type=False)

    op.create_table(
        "org_invites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("role", org_role, nullable=False, server_default="member"),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column("status", invite_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_org_invites_org_id", "org_invites", ["org_id"])
    op.create_index("ix_org_invites_email", "org_invites", ["email"])
    op.create_index("ix_org_invites_status", "org_invites", ["status"])


def downgrade() -> None:
    op.drop_table("org_invites")
    op.execute("DROP TYPE IF EXISTS invite_status")
    op.drop_column("memberships", "email")
    op.drop_column("organizations", "plan")
