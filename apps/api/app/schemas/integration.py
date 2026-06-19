"""Meta integration schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class OAuthStartOut(BaseModel):
    authorize_url: str


class ConnectMockIn(BaseModel):
    brand_id: uuid.UUID
    # Optional code-like seed so mock accounts are deterministic per test.
    code: str = "devmock"
