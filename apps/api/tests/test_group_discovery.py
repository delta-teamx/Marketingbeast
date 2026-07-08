"""Real Facebook-group discovery via the (mocked) Tavily web-search API.

Meta has no Groups API, so we search the public web for facebook.com/groups pages.
These tests mock the HTTP layer to prove we parse real group URLs, drop junk, and
turn them into suggestions carrying a direct group link.
"""

from __future__ import annotations

import httpx
import pytest

from app.core.config import get_settings
from app.services.group_discovery import _canonical_group_url, discover_groups
from app.services.group_finder import NicheProfile, suggest_groups

TAVILY_RESULTS = {
    "results": [
        {
            "url": "https://www.facebook.com/groups/aimarketingpros/",
            "title": "AI Marketing Pros | Facebook",
            "content": "A community of AI marketing agencies sharing leads and tips.",
        },
        {"url": "https://facebook.com/groups/123456789", "title": "Agency Growth Lab"},
        # Not a group — must be filtered out.
        {"url": "https://facebook.com/some-business-page", "title": "A Page"},
        # Duplicate of the first (after canonicalization) — must be deduped.
        {"url": "https://m.facebook.com/groups/aimarketingpros?ref=share", "title": "dupe"},
    ]
}


def _handler(request: httpx.Request) -> httpx.Response:
    assert request.url.path.endswith("/search")
    return httpx.Response(200, json=TAVILY_RESULTS)


@pytest.fixture
def tavily(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GROUP_SEARCH_PROVIDER", "tavily")
    monkeypatch.setenv("GROUP_SEARCH_API_KEY", "tvly-test")
    get_settings.cache_clear()
    from app.services import group_discovery as mod

    real = httpx.AsyncClient
    monkeypatch.setattr(
        mod.httpx,
        "AsyncClient",
        lambda *a, **k: real(*a, **{**k, "transport": httpx.MockTransport(_handler)}),
    )
    yield
    get_settings.cache_clear()


def test_canonical_group_url_normalizes_and_rejects() -> None:
    assert (
        _canonical_group_url("https://m.facebook.com/groups/foo?ref=x")
        == "https://www.facebook.com/groups/foo"
    )
    assert _canonical_group_url("https://facebook.com/some-page") is None
    assert _canonical_group_url("https://facebook.com/groups/search") is None


async def test_discovery_off_returns_empty() -> None:
    get_settings.cache_clear()  # default provider is "none"
    assert await discover_groups(category="AI marketing", keywords=["agency"]) == []


async def test_tavily_returns_real_deduped_groups(tavily) -> None:
    groups = await discover_groups(category="AI marketing agency", keywords=["leads", "agency"])
    urls = [g.url for g in groups]
    assert urls == [
        "https://www.facebook.com/groups/aimarketingpros",
        "https://www.facebook.com/groups/123456789",
    ]
    assert groups[0].name == "AI Marketing Pros"  # " | Facebook" stripped


async def test_suggest_groups_uses_real_discovery(tavily) -> None:
    niche = NicheProfile(
        category="AI marketing agency", summary="", keywords=["leads", "agency"]
    )
    suggestions = await suggest_groups(brand_name="Beast Agency", niche=niche)
    assert len(suggestions) == 2
    prefix = "https://www.facebook.com/groups/"
    assert all(s.group_url and s.group_url.startswith(prefix) for s in suggestions)
    # Ranked by discovery order (first result scores highest).
    assert suggestions[0].relevance_score >= suggestions[1].relevance_score
