"""User-facing schemas (Pydantic v2)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict

from app.models.membership import OrgRole


class MembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    org_id: uuid.UUID
    role: OrgRole


class MeOut(BaseModel):
    id: str
    email: str | None
    memberships: list[MembershipOut]
