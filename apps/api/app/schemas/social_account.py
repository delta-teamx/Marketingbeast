"""SocialAccount schemas (no tokens are ever serialized)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.models.social_account import SocialProvider


class SocialAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    provider: SocialProvider
    external_id: str | None
    display_name: str | None
    status: str
