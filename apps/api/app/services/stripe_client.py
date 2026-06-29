"""Billing client adapter — mock (default) + live Stripe.

mock: `create_checkout` reports the upgrade as immediately completed (the route
applies it) so dev/tests work with no Stripe account. "stripe": real Checkout
sessions + signed webhooks (requires the `stripe` package + keys).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from app.core.config import get_settings


@dataclass
class CheckoutResult:
    url: str
    completed: bool  # mock applies instantly; live completes via webhook


@runtime_checkable
class BillingClient(Protocol):
    def create_checkout(self, *, org_id: str, plan: str, price_id: str) -> CheckoutResult: ...
    def parse_webhook(self, *, payload: bytes, signature: str) -> dict[str, Any]: ...


class MockBillingClient:
    def create_checkout(self, *, org_id: str, plan: str, price_id: str) -> CheckoutResult:
        s = get_settings()
        return CheckoutResult(url=f"{s.billing_success_url}&plan={plan}", completed=True)

    def parse_webhook(self, *, payload: bytes, signature: str) -> dict[str, Any]:
        return {"type": "noop"}


class LiveStripeClient:
    def __init__(self) -> None:
        self._s = get_settings()

    def _stripe(self):
        try:
            import stripe  # noqa: PLC0415
        except ImportError as exc:  # pragma: no cover - live only
            raise RuntimeError("Install the `stripe` package for live billing") from exc
        stripe.api_key = self._s.stripe_secret_key
        return stripe

    def create_checkout(self, *, org_id: str, plan: str, price_id: str) -> CheckoutResult:
        stripe = self._stripe()
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=self._s.billing_success_url,
            cancel_url=self._s.billing_cancel_url,
            client_reference_id=org_id,
            metadata={"org_id": org_id, "plan": plan},
        )
        return CheckoutResult(url=session.url, completed=False)

    def parse_webhook(self, *, payload: bytes, signature: str) -> dict[str, Any]:
        stripe = self._stripe()
        event = stripe.Webhook.construct_event(
            payload, signature, self._s.stripe_webhook_secret
        )
        # to_dict_recursive() converts the nested StripeObjects (data.object,
        # metadata, …) into plain dicts so the webhook handler's .get() chain is
        # reliable across stripe SDK versions; dict(event) only copies the top level.
        return event.to_dict_recursive()


def get_billing_client() -> BillingClient:
    if get_settings().billing_provider == "stripe":
        return LiveStripeClient()
    return MockBillingClient()
