"""Processed webhook events — idempotency ledger for inbound provider webhooks.

Stripe (and most providers) deliver each event at least once, and may redeliver.
We record every event id we've handled so re-deliveries are no-ops and we never
grant a plan's credits twice for a single purchase.
"""

from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class ProcessedWebhookEvent(Base, TimestampMixin):
    __tablename__ = "processed_webhook_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    # Stripe event id (e.g. "evt_..."), unique so a redelivery collides.
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(30), default="stripe", nullable=False)
