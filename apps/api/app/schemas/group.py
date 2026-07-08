"""Schemas for niche detection + Facebook group suggestions / Tier B queue."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.group import GroupTaskStatus, SuggestionStatus


class NicheProfileOut(BaseModel):
    category: str
    summary: str
    keywords: list[str]


class GenerateSuggestionsIn(BaseModel):
    brand_id: uuid.UUID


class GroupSuggestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    name: str
    search_keyword: str
    group_url: str | None = None
    estimated_size: str | None
    relevance_score: int
    lead_quality_score: int
    rationale: str | None
    suggested_post_angle: str | None
    status: SuggestionStatus


class SuggestionStatusUpdate(BaseModel):
    status: SuggestionStatus


class GroupQueueCreate(BaseModel):
    brand_id: uuid.UUID
    group_suggestion_id: uuid.UUID
    body: str = Field(min_length=1, max_length=5000)
    media_urls: list[str] | None = None


class GroupPostTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    group_suggestion_id: uuid.UUID
    body: str
    media_urls: list[str] | None
    status: GroupTaskStatus
    external_ref: str | None


class GroupTaskUpdate(BaseModel):
    """Status update from the Tier B extension as it claims / completes a task."""

    status: GroupTaskStatus
    external_ref: str | None = None
