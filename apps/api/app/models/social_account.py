"""SocialAccount — a connected FB Page or IG account (Tier A).

Phase 0 stub: the table and encryption path exist, but the OAuth connect flow
lands in Phase 1. OAuth tokens are stored encrypted at rest (Fernet) and never
logged.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.brand import Brand


class SocialProvider(str, enum.Enum):
    facebook_page = "facebook_page"
    instagram = "instagram"


class SocialAccount(Base, TimestampMixin):
    __tablename__ = "social_accounts"

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[SocialProvider] = mapped_column(
        SAEnum(SocialProvider, name="social_provider"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Encrypted via app.services.crypto (Fernet). Never store or log plaintext.
    access_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    scopes: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="disconnected", nullable=False)

    brand: Mapped[Brand] = relationship(back_populates="social_accounts")
