"""Ads models: connected ad accounts, campaigns, and creative variations.

Mirrors the Meta Marketing API objects we manage. Metrics are stored as JSON
snapshots (impressions/clicks/spend/ctr/conversions).
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    pass


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    paused = "paused"


class CreativeStatus(str, enum.Enum):
    active = "active"
    paused = "paused"


class AdAccount(Base, TimestampMixin):
    __tablename__ = "ad_accounts"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="connected", nullable=False)


class AdCampaign(Base, TimestampMixin):
    __tablename__ = "ad_campaigns"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ad_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ad_accounts.id", ondelete="CASCADE"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(String(50), default="LEADS", nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus, name="campaign_status"),
        default=CampaignStatus.active,
        nullable=False,
        index=True,
    )
    daily_budget: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    creatives: Mapped[list[AdCreative]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class AdCreative(Base, TimestampMixin):
    __tablename__ = "ad_creatives"

    id: Mapped[uuid.UUID] = uuid_pk()
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ad_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    variation_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[CreativeStatus] = mapped_column(
        SAEnum(CreativeStatus, name="creative_status"),
        default=CreativeStatus.active,
        nullable=False,
    )
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    campaign: Mapped[AdCampaign] = relationship(back_populates="creatives")
