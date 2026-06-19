"""Billing: Stripe Checkout + webhook → plan & credits.

mock mode applies the upgrade instantly (dev/tests). stripe mode returns a
Checkout URL and applies the plan when the signed webhook arrives.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_org_role
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import AuthenticatedUser
from app.models.membership import OrgRole
from app.models.organization import Organization
from app.models.webhook import ProcessedWebhookEvent
from app.schemas.billing import CheckoutIn, CheckoutOut, PlanInfo
from app.services.billing import (
    PLAN_CREDITS,
    PLAN_LIMITS,
    complete_upgrade,
    plan_price_id,
)
from app.services.stripe_client import get_billing_client

logger = get_logger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanInfo])
async def list_plans() -> list[PlanInfo]:
    return [
        PlanInfo(
            key=key,
            max_brands=limits.max_brands,
            max_seats=limits.max_seats,
            monthly_credits=PLAN_CREDITS.get(key, 0),
        )
        for key, limits in PLAN_LIMITS.items()
    ]


@router.post("/checkout", response_model=CheckoutOut)
async def checkout(
    payload: CheckoutIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CheckoutOut:
    await require_org_role(payload.org_id, session=session, user=user, allowed=(OrgRole.owner,))
    org = await session.get(Organization, payload.org_id)

    result = get_billing_client().create_checkout(
        org_id=str(org.id), plan=payload.plan, price_id=plan_price_id(payload.plan)
    )
    if result.completed:  # mock — apply immediately
        org = await complete_upgrade(session, org, payload.plan)

    return CheckoutOut(
        url=result.url,
        completed=result.completed,
        plan=org.plan,
        credit_balance=org.credit_balance,
    )


@router.post("/webhook")
async def webhook(
    request: Request,
    stripe_signature: str = Header(default="", alias="Stripe-Signature"),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Stripe calls this (no user auth — verified by signature in live mode)."""
    if get_settings().billing_provider != "stripe":
        return {"status": "ignored"}

    payload = await request.body()
    try:
        event = get_billing_client().parse_webhook(payload=payload, signature=stripe_signature)
    except Exception as exc:  # noqa: BLE001 - any verification failure → 400
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {exc}") from exc

    # Idempotency: Stripe delivers events at least once and may redeliver, and a
    # single purchase fires several event types. Record each event id and bail if
    # we've already handled it, so we never grant a plan's credits twice.
    event_id = event.get("id")
    if event_id:
        session.add(ProcessedWebhookEvent(event_id=str(event_id), provider="stripe"))
        try:
            await session.flush()
        except IntegrityError:
            await session.rollback()
            return {"status": "duplicate"}

    if event.get("type") in ("checkout.session.completed", "customer.subscription.updated"):
        obj = event.get("data", {}).get("object", {})
        meta = obj.get("metadata", {}) or {}
        org_id = meta.get("org_id") or obj.get("client_reference_id")
        plan = meta.get("plan")
        if org_id and plan:
            org = await session.get(Organization, uuid.UUID(org_id))
            if org is not None:
                if obj.get("customer"):
                    org.stripe_customer_id = obj["customer"]
                if obj.get("subscription"):
                    org.stripe_subscription_id = obj["subscription"]
                await complete_upgrade(session, org, plan)
                logger.info("billing: org %s upgraded to %s via webhook", org_id, plan)
    # Persist the idempotency record even for events that did no upgrade work.
    await session.commit()
    return {"status": "ok"}
