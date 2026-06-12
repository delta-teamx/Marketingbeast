"""OnboardingProfile — what we learn about a business during onboarding.

Captures goals, platforms, cadence, budget, and pain points so the AI can tune
strategy and the audit per business (brief: conversational onboarding).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.brand import Brand


class OnboardingProfile(Base, TimestampMixin):
    __tablename__ = "onboarding_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    goal: Mapped[str | None] = mapped_column(String(100), nullable=True)
    platforms: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    posting_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    monthly_budget: Mapped[str | None] = mapped_column(String(50), nullable=True)
    biggest_challenge: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_audience: Mapped[str | None] = mapped_column(Text, nullable=True)

    brand: Mapped[Brand] = relationship()
