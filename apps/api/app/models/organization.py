"""Organization — the multi-tenant boundary (an agency or a business)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.membership import Membership


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False, index=True)
    is_personal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # White-label settings for agency tier (Phase 8); nullable for now.
    white_label_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    # Credit balance for metered AI media generation (Phase 7).
    credit_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Billing tier (Phase 8): free | growth | agency. Drives per-brand/seat limits.
    plan: Mapped[str] = mapped_column(String(20), default="free", nullable=False)

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
    brands: Mapped[list[Brand]] = relationship(
        back_populates="organization", cascade="all, delete-orphan"
    )
