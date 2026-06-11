"""Audit report schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    overall_score: int
    overall_grade: str
    sections: list[dict[str, Any]]
    findings: list[str]
    recommendations: list[str]
    strategy_brief: str
    content_plan: list[dict[str, Any]]
    created_at: datetime
