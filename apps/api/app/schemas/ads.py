"""Ads schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.ads import CampaignStatus, CreativeStatus


class AdAccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    external_id: str
    name: str | None
    status: str


class CampaignCreate(BaseModel):
    ad_account_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    objective: str = Field(default="LEADS", max_length=50)
    daily_budget: float = Field(default=10.0, ge=1)
    concept: str = Field(default="", max_length=1000)
    n_variations: int = Field(default=12, ge=1, le=20)


class CreativeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    variation_index: int
    headline: str
    primary_text: str
    status: CreativeStatus
    metrics_json: dict[str, Any]


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    ad_account_id: uuid.UUID
    name: str
    objective: str
    status: CampaignStatus
    daily_budget: float
    metrics_json: dict[str, Any]


class CampaignDetailOut(CampaignOut):
    creatives: list[CreativeOut]


class StatusUpdate(BaseModel):
    status: CampaignStatus
