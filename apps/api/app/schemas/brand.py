"""Brand schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class BrandCreate(BaseModel):
    org_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    website_url: str | None = Field(default=None, max_length=500)
    industry_vertical: str | None = Field(default=None, max_length=100)


class BrandOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    website_url: str | None
    industry_vertical: str | None
