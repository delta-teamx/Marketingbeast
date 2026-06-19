"""Agency / white-label schemas."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.invite import InviteStatus
from app.models.membership import OrgRole


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    email: str | None
    role: OrgRole


class RoleUpdate(BaseModel):
    role: OrgRole


class InviteCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: OrgRole = OrgRole.member


class InviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    email: str
    role: OrgRole
    status: InviteStatus


class PlanUpdate(BaseModel):
    plan: str = Field(pattern="^(free|growth|agency)$")


class WhiteLabelIn(BaseModel):
    brand_name: str | None = Field(default=None, max_length=200)
    logo_url: str | None = Field(default=None, max_length=500)
    primary_color: str | None = Field(default=None, max_length=20)
    custom_domain: str | None = Field(default=None, max_length=200)


class OrgSettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    plan: str
    credit_balance: int
    white_label_json: dict[str, Any] | None
