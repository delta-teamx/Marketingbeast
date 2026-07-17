"""The public /api/config feature flags drive coming-soon UI (e.g. Ads Manager)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import get_settings


async def test_ads_enabled_in_mock_mode(client: AsyncClient) -> None:
    # The suite runs with META_MODE + MEDIA_PROVIDER defaulting to mock.
    resp = await client.get("/api/config")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ads_enabled"] is True
    # No real render provider in tests → reels are coming soon.
    assert body["media_enabled"] is False


async def test_ads_disabled_in_live_mode(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("META_MODE", "live")
    get_settings.cache_clear()
    try:
        resp = await client.get("/api/config")
        assert resp.status_code == 200
        assert resp.json()["ads_enabled"] is False
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
