"""Onboarding schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.brand import BrandOut


class OnboardingIn(BaseModel):
    business_name: str = Field(min_length=1, max_length=200)
    website_url: str | None = Field(default=None, max_length=500)
    industry: str | None = Field(default=None, max_length=100)
    goal: str | None = Field(default=None, max_length=100)
    platforms: list[str] = Field(default_factory=list)
    posting_frequency: str | None = Field(default=None, max_length=50)
    monthly_budget: str | None = Field(default=None, max_length=50)
    biggest_challenge: str | None = Field(default=None, max_length=2000)
    target_audience: str | None = Field(default=None, max_length=2000)


class OnboardingProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    goal: str | None
    platforms: list[str] | None
    posting_frequency: str | None
    monthly_budget: str | None
    biggest_challenge: str | None
    target_audience: str | None


class OnboardingOut(BaseModel):
    brand: BrandOut
    profile: OnboardingProfileOut
