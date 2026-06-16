"""Billing tiers + per-org limits (Phase 8).

Plans gate how many brands and seats an organization may have. Real payment
(Stripe) lands later; `set_plan` is a mock upgrade for now.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.brand import Brand
from app.models.media import CreditLedger
from app.models.membership import Membership
from app.models.organization import Organization

# Monthly credit grant per plan (applied on upgrade).
PLAN_CREDITS: dict[str, int] = {"free": 0, "growth": 200, "agency": 1000}


@dataclass(frozen=True)
class PlanLimits:
    max_brands: int
    max_seats: int


PLAN_LIMITS: dict[str, PlanLimits] = {
    "free": PlanLimits(max_brands=1, max_seats=1),
    "growth": PlanLimits(max_brands=3, max_seats=3),
    "agency": PlanLimits(max_brands=1000, max_seats=1000),
}

VALID_PLANS = tuple(PLAN_LIMITS)


def limits_for(plan: str) -> PlanLimits:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


async def _count(session: AsyncSession, model, org_id: uuid.UUID) -> int:
    return (
        await session.scalar(select(func.count(model.id)).where(model.org_id == org_id))
    ) or 0


async def ensure_can_add_brand(session: AsyncSession, org: Organization) -> None:
    limit = limits_for(org.plan).max_brands
    if await _count(session, Brand, org.id) >= limit:
        raise HTTPException(
            status_code=402,
            detail=f"Your {org.plan} plan allows {limit} brand(s). Upgrade to add more.",
        )


async def ensure_can_add_seat(session: AsyncSession, org: Organization) -> None:
    limit = limits_for(org.plan).max_seats
    if await _count(session, Membership, org.id) >= limit:
        raise HTTPException(
            status_code=402,
            detail=f"Your {org.plan} plan allows {limit} seat(s). Upgrade to add more.",
        )


async def set_plan(session: AsyncSession, org: Organization, plan: str) -> Organization:
    if plan not in PLAN_LIMITS:
        raise HTTPException(status_code=400, detail=f"Unknown plan '{plan}'")
    org.plan = plan
    await session.commit()
    await session.refresh(org)
    return org


def plan_price_id(plan: str) -> str:
    s = get_settings()
    return {"growth": s.stripe_price_growth, "agency": s.stripe_price_agency}.get(plan, "")


async def complete_upgrade(session: AsyncSession, org: Organization, plan: str) -> Organization:
    """Apply a paid plan: set the tier and grant its monthly credits (idempotent
    per call). Used by mock checkout and the Stripe webhook."""
    if plan not in PLAN_LIMITS:
        raise HTTPException(status_code=400, detail=f"Unknown plan '{plan}'")
    org.plan = plan
    grant = PLAN_CREDITS.get(plan, 0)
    if grant:
        org.credit_balance += grant
        session.add(CreditLedger(org_id=org.id, delta=grant, reason=f"{plan} plan credits"))
    await session.commit()
    await session.refresh(org)
    return org
