"""Analytics schemas."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.analytics import ReportPeriod


class DashboardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    followers: int
    follower_growth: int
    total_reach: int
    total_engagement: int
    engagement_rate: float
    time_series: list[dict[str, Any]]
    top_posts: list[dict[str, Any]]
    per_account: list[dict[str, Any]]


class ReportGenerateIn(BaseModel):
    period: ReportPeriod = ReportPeriod.weekly


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    period: ReportPeriod
    starts_on: date
    ends_on: date
    metrics_json: dict[str, Any]
    summary: str


class CompetitorIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    handle: str | None = Field(default=None, max_length=200)
    platform: str | None = Field(default=None, max_length=50)
    followers: int = Field(default=0, ge=0)
    posting_frequency: str | None = Field(default=None, max_length=50)
    engagement_rate: float = Field(default=0.0, ge=0)


class CompetitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    name: str
    handle: str | None
    platform: str | None
    followers: int
    posting_frequency: str | None
    engagement_rate: float
