"""Billing schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CheckoutIn(BaseModel):
    org_id: uuid.UUID
    plan: str = Field(pattern="^(growth|agency)$")


class CheckoutOut(BaseModel):
    url: str
    completed: bool
    plan: str
    credit_balance: int


class PlanInfo(BaseModel):
    key: str
    max_brands: int
    max_seats: int
    monthly_credits: int
