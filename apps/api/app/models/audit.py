"""AuditReport — the flagship URL→Presence audit result for a Brand.

Combines deterministic checks (profile fields, connected platforms, posting
cadence) with LLM qualitative judgment into reproducible numeric sub-scores, an
overall letter grade, a strategy brief, and a first-week content plan that can be
seeded into the content engine.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.brand import Brand


class AuditReport(Base, TimestampMixin):
    __tablename__ = "audit_reports"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    overall_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overall_grade: Mapped[str] = mapped_column(String(2), default="F", nullable=False)
    # [{key, label, score, notes}, ...]
    sections: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    findings: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    strategy_brief: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # [{day, idea, caption, hashtags}, ...]
    content_plan: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)

    brand: Mapped[Brand] = relationship()
