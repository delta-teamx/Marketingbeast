"""Stripe webhooks must be idempotent: a single purchase fires several events and
may be redelivered, but the plan's credits must be granted exactly once.
"""

from __future__ import annotations

import types
import uuid

from httpx import AsyncClient

import app.api.routers.billing as billing_router
from app.db.session import AsyncSessionLocal
from app.models.organization import Organization


class _FakeClient:
    def __init__(self, event: dict) -> None:
        self.event = event

    def parse_webhook(self, *, payload: bytes, signature: str) -> dict:
        return self.event


async def _provision_org(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)
    return (await client.get("/api/organizations", headers=headers)).json()[0]["id"]


async def test_duplicate_webhook_grants_credits_once(
    client: AsyncClient, auth_headers: dict[str, str], monkeypatch
) -> None:
    org_id = await _provision_org(client, auth_headers)

    event = {
        "id": "evt_test_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"org_id": org_id, "plan": "growth"},
                "customer": "cus_1",
                "subscription": "sub_1",
            }
        },
    }

    # Force "stripe" mode and a fake client (no real signature / Stripe SDK).
    monkeypatch.setattr(
        billing_router, "get_settings", lambda: types.SimpleNamespace(billing_provider="stripe")
    )
    monkeypatch.setattr(billing_router, "get_billing_client", lambda: _FakeClient(event))

    async def deliver() -> dict:
        resp = await client.post(
            "/api/billing/webhook",
            content=b"{}",
            headers={"Stripe-Signature": "t=1,v1=sig"},
        )
        assert resp.status_code == 200
        return resp.json()

    first = await deliver()
    second = await deliver()  # same event id — redelivery
    third = await deliver()  # and again

    assert first["status"] == "ok"
    assert second["status"] == "duplicate"
    assert third["status"] == "duplicate"

    # Credits granted exactly once: starter (100) + growth (200) = 300, not 500/700.
    async with AsyncSessionLocal() as session:
        org = await session.get(Organization, uuid.UUID(org_id))
        assert org.plan == "growth"
        assert org.credit_balance == 100 + 200
        assert org.stripe_customer_id == "cus_1"
