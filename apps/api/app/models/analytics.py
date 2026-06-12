"""Analytics models: daily metric snapshots, generated reports, competitors."""

from __future__ import annotations

import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.social_account import SocialAccount


class ReportPeriod(str, enum.Enum):
    weekly = "weekly"
    monthly = "monthly"


class MetricSnapshot(Base, TimestampMixin):
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        UniqueConstraint("social_account_id", "snapshot_date", name="uq_snapshot_account_day"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    followers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reach: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engagement: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    posts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    social_account: Mapped[SocialAccount] = relationship()


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[ReportPeriod] = mapped_column(
        SAEnum(ReportPeriod, name="report_period"), nullable=False
    )
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)

    brand: Mapped[Brand] = relationship()


class Competitor(Base, TimestampMixin):
    __tablename__ = "competitors"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    handle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    followers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    posting_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
