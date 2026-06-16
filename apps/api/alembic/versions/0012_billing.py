"""billing: stripe ids on organizations

Revision ID: 0012_billing
Revises: 0011_agency
Create Date: 2026-06-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012_billing"
down_revision: str | None = "0011_agency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("organizations", sa.Column("stripe_customer_id", sa.String(64), nullable=True))
    op.add_column(
        "organizations", sa.Column("stripe_subscription_id", sa.String(64), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("organizations", "stripe_subscription_id")
    op.drop_column("organizations", "stripe_customer_id")
