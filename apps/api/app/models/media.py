"""AI media generation: render jobs, generated assets, and a credit ledger."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.brand import Brand


class MediaJobStatus(str, enum.Enum):
    queued = "queued"
    rendering = "rendering"
    ready = "ready"
    failed = "failed"


class MediaJob(Base, TimestampMixin):
    __tablename__ = "media_jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[MediaJobStatus] = mapped_column(
        SAEnum(MediaJobStatus, name="media_job_status"),
        default=MediaJobStatus.queued,
        nullable=False,
        index=True,
    )
    prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    script: Mapped[str] = mapped_column(Text, default="", nullable=False)
    storyboard_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, nullable=False
    )
    external_job_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    asset_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cost_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand: Mapped[Brand] = relationship()


class MediaAsset(Base, TimestampMixin):
    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[str] = mapped_column(String(20), default="video", nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="ai_generated", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    media_job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("media_jobs.id", ondelete="SET NULL"), nullable=True
    )


class CreditLedger(Base, TimestampMixin):
    __tablename__ = "credit_ledger"

    id: Mapped[uuid.UUID] = uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
