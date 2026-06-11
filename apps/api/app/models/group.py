"""Facebook group lead-finder models.

GroupSuggestion = an AI-recommended group for a brand to join + post in for
leads (Tier A — pure advisory; we never query Meta for groups).

GroupPostTask = a queued post for the *Tier B* browser extension to publish
locally under the §9 pacing guardrails. The backend only stores the queue; it
NEVER posts to groups itself.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.brand import Brand


class SuggestionStatus(str, enum.Enum):
    suggested = "suggested"
    tracked = "tracked"
    dismissed = "dismissed"


class GroupTaskStatus(str, enum.Enum):
    queued = "queued"
    claimed = "claimed"  # picked up by the Tier B extension
    posted = "posted"
    skipped = "skipped"


class GroupSuggestion(Base, TimestampMixin):
    __tablename__ = "group_suggestions"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    # Keyword the user types into Facebook's group search to find it.
    search_keyword: Mapped[str] = mapped_column(String(300), nullable=False)
    estimated_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relevance_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lead_quality_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_post_angle: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SuggestionStatus] = mapped_column(
        SAEnum(SuggestionStatus, name="group_suggestion_status"),
        default=SuggestionStatus.suggested,
        nullable=False,
        index=True,
    )

    brand: Mapped[Brand] = relationship()


class GroupPostTask(Base, TimestampMixin):
    __tablename__ = "group_post_tasks"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    group_suggestion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("group_suggestions.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    media_urls: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    status: Mapped[GroupTaskStatus] = mapped_column(
        SAEnum(GroupTaskStatus, name="group_task_status"),
        default=GroupTaskStatus.queued,
        nullable=False,
        index=True,
    )
    # Set by the Tier B extension after a local post (we never set this).
    external_ref: Mapped[str | None] = mapped_column(String(300), nullable=True)

    suggestion: Mapped[GroupSuggestion] = relationship()
