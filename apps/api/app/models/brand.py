"""Brand — a managed business within an Organization."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.social_account import SocialAccount


class Brand(Base, TimestampMixin):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry_vertical: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Brand voice profile + colors are populated by the audit engine (Phase 2/3).
    voice_profile_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    colors_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="brands")
    social_accounts: Mapped[list[SocialAccount]] = relationship(
        back_populates="brand", cascade="all, delete-orphan"
    )
