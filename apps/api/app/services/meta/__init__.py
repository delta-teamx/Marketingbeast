"""Meta (Facebook/Instagram) integration — Tier A, official Graph API.

`get_meta_client()` returns the configured adapter: a mock for local dev/tests
(META_MODE=mock, default) or the live Graph API client (META_MODE=live).
"""

from __future__ import annotations

from app.core.config import get_settings
from app.services.meta.base import (
    ConnectedAccount,
    ConversationData,
    InsightsData,
    MetaClient,
    PublishResult,
)


def get_meta_client() -> MetaClient:
    settings = get_settings()
    if settings.meta_mode == "live":
        from app.services.meta.live import LiveMetaClient

        return LiveMetaClient()
    from app.services.meta.mock import MockMetaClient

    return MockMetaClient()


__all__ = [
    "ConnectedAccount",
    "ConversationData",
    "InsightsData",
    "MetaClient",
    "PublishResult",
    "get_meta_client",
]
