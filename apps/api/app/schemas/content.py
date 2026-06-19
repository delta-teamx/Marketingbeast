"""Content publishing schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.content import ContentStatus, ContentType, TargetStatus


class ContentCreate(BaseModel):
    brand_id: uuid.UUID
    body: str = Field(default="", max_length=5000)
    content_type: ContentType = ContentType.post
    media_urls: list[str] | None = None
    target_account_ids: list[uuid.UUID] = Field(min_length=1)
    scheduled_time: datetime | None = None


class ContentTargetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    social_account_id: uuid.UUID
    status: TargetStatus
    external_post_id: str | None
    permalink: str | None
    error: str | None


class ContentGenerateIn(BaseModel):
    brand_id: uuid.UUID
    prompt: str = Field(default="", max_length=2000)
    count: int = Field(default=7, ge=1, le=14)


class ContentItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    content_type: ContentType
    status: ContentStatus
    body: str
    media_urls: list[str] | None
    scheduled_time: datetime | None
    published_at: datetime | None
    approved: bool
    hashtags: list[str] | None
    suggested_time: str | None
    targets: list[ContentTargetOut]
