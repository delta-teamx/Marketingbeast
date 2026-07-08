"""Real Facebook-group discovery via the (mocked) Tavily web-search API.

Meta has no Groups API, so we search the public web for facebook.com/groups links —
both direct group pages and group URLs mentioned inside round-up articles — using
lead-focused queries (where the business's CUSTOMERS gather).
"""

from __future__ import annotations

import httpx
import pytest

from app.core.config import get_settings
from app.services.group_discovery import _canonical_group_url, discover_groups
from app.services.group_finder import NicheProfile, lead_search_queries, suggest_groups

# One direct group page, one round-up article that mentions group links in its
# content, and one non-group page (must be ignored).
TAVILY_RESULTS = {
    "results": [
        {
            "url": "https://www.facebook.com/groups/homeownershelp/",
            "title": "Homeowners Help | Facebook",
            "content": "Homeowners discussing repairs, HVAC, and contractor recommendations.",
        },
        {
            "url": "https://blog.example.com/best-groups-for-homeowners",
            "title": "Top Facebook groups for homeowners",
            "content": "Join https://facebook.com/groups/hvachomeowners and "
            "https://www.facebook.com/groups/123456789 for local help.",
        },
        {"url": "https://facebook.com/some-business-page", "title": "A Page"},
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
    assert await discover_groups(queries=["homeowners facebook group"]) == []


async def test_tavily_extracts_real_groups_from_urls_and_content(tavily) -> None:
    groups = await discover_groups(queries=["homeowners facebook group"])
    urls = [g.url for g in groups]
    assert urls == [
        "https://www.facebook.com/groups/homeownershelp",
        "https://www.facebook.com/groups/hvachomeowners",
        "https://www.facebook.com/groups/123456789",
    ]
    assert groups[0].name == "Homeowners Help"  # direct group page keeps its title


async def test_suggest_groups_returns_real_groups(tavily) -> None:
    niche = NicheProfile(category="HVAC", summary="", keywords=["hvac", "heating"])
    suggestions = await suggest_groups(
        brand_name="CoolAir HVAC", niche=niche, audience="homeowners", goal="more_leads"
    )
    assert len(suggestions) == 3
    prefix = "https://www.facebook.com/groups/"
    assert all(s.group_url and s.group_url.startswith(prefix) for s in suggestions)
    assert suggestions[0].relevance_score >= suggestions[-1].relevance_score


async def test_lead_queries_mock_mode() -> None:
    niche = NicheProfile(category="HVAC", summary="", keywords=["hvac"])
    qs = await lead_search_queries(
        brand_name="CoolAir", niche=niche, audience="homeowners", goal="more_leads"
    )
    assert qs and any("homeowners" in q for q in qs)
