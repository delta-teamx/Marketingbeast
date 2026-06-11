"""ContentItem + ContentTarget — the publishing unit and its per-account results.

A ContentItem is a draft/scheduled/published post belonging to a Brand. Each
ContentTarget records the attempt to publish that item to one SocialAccount,
including the external post id (used for idempotency — never double-post).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.brand import Brand
    from app.models.social_account import SocialAccount


class ContentStatus(str, enum.Enum):
    draft = "draft"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class ContentType(str, enum.Enum):
    post = "post"
    reel = "reel"
    story = "story"


class TargetStatus(str, enum.Enum):
    pending = "pending"
    published = "published"
    failed = "failed"


class ContentItem(Base, TimestampMixin):
    __tablename__ = "content_items"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_type: Mapped[ContentType] = mapped_column(
        SAEnum(ContentType, name="content_type"), default=ContentType.post, nullable=False
    )
    status: Mapped[ContentStatus] = mapped_column(
        SAEnum(ContentStatus, name="content_status"),
        default=ContentStatus.draft,
        nullable=False,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    media_urls: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    scheduled_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Approval workflow: draft → approved → scheduled (brief §6.2).
    approved: Mapped[bool] = mapped_column(default=False, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Hashtags + a rules-based best-time suggestion from the content engine.
    hashtags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    suggested_time: Mapped[str | None] = mapped_column(String(50), nullable=True)

    brand: Mapped[Brand] = relationship()
    targets: Mapped[list[ContentTarget]] = relationship(
        back_populates="content_item", cascade="all, delete-orphan"
    )


class ContentTarget(Base, TimestampMixin):
    __tablename__ = "content_targets"

    id: Mapped[uuid.UUID] = uuid_pk()
    content_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("social_accounts.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[TargetStatus] = mapped_column(
        SAEnum(TargetStatus, name="target_status"), default=TargetStatus.pending, nullable=False
    )
    # Set once published — presence of this guards against double-posting.
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    permalink: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    content_item: Mapped[ContentItem] = relationship(back_populates="targets")
    social_account: Mapped[SocialAccount] = relationship()
