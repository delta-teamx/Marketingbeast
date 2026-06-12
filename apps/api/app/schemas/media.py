"""AI media schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.media import MediaJobStatus


class VideoGenerateIn(BaseModel):
    note: str = Field(default="", max_length=2000)
    product_url: str | None = Field(default=None, max_length=500)
    style: str = Field(default="ugc", max_length=30)


class MediaJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    provider: str
    status: MediaJobStatus
    prompt: str
    script: str
    storyboard_json: list[dict[str, Any]]
    asset_url: str | None
    cost_credits: int
    error: str | None


class MediaAssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    kind: str
    url: str
    source: str
    provider: str | None


class CreditsOut(BaseModel):
    org_id: uuid.UUID
    credit_balance: int


class TopupIn(BaseModel):
    amount: int = Field(ge=1, le=100000)
