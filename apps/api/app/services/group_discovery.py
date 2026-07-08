"""Real Facebook-group discovery via a web-search API.

Meta shut down the Groups API, so there is no way to query Facebook for groups.
To surface REAL, existing groups we search the *public web* (not Facebook itself)
for facebook.com/groups pages — legitimate, and it returns groups that actually
exist. GROUP_SEARCH_PROVIDER selects: "none" (default; feature off, suggestions
stay AI-advisory) or "tavily".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Matches a Facebook group URL and captures up to the group id/slug.
_GROUP_URL_RE = re.compile(
    r"https?://(?:www\.|m\.|web\.|mbasic\.)?facebook\.com/groups/([A-Za-z0-9._-]+)",
    re.IGNORECASE,
)


@dataclass
class DiscoveredGroup:
    name: str
    url: str
    snippet: str = ""


def _canonical_group_url(url: str) -> str | None:
    """Return the canonical https://www.facebook.com/groups/<id> URL, or None."""
    m = _GROUP_URL_RE.search(url or "")
    if not m:
        return None
    slug = m.group(1)
    if slug in {"feed", "search", "discover", "create"}:  # not an actual group
        return None
    return f"https://www.facebook.com/groups/{slug}"


def _dedupe(groups: list[DiscoveredGroup]) -> list[DiscoveredGroup]:
    seen: set[str] = set()
    out: list[DiscoveredGroup] = []
    for g in groups:
        if g.url in seen:
            continue
        seen.add(g.url)
        out.append(g)
    return out


async def discover_groups(
    *, category: str, keywords: list[str], limit: int = 10
) -> list[DiscoveredGroup]:
    """Discover real Facebook groups for a niche. Returns [] when the feature is
    off (GROUP_SEARCH_PROVIDER=none) so callers fall back to advisory suggestions."""
    provider = get_settings().group_search_provider
    if provider in ("", "none"):
        return []
    if provider == "tavily":
        return await _tavily(category, keywords, limit)
    logger.warning("unknown GROUP_SEARCH_PROVIDER=%s; skipping discovery", provider)
    return []


async def _tavily(category: str, keywords: list[str], limit: int) -> list[DiscoveredGroup]:
    settings = get_settings()
    if not settings.group_search_api_key:
        raise RuntimeError("GROUP_SEARCH_API_KEY is required for the tavily group search provider")
    kw = " ".join(keywords[:4])
    query = f"active Facebook groups for {category} {kw}".strip()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.group_search_base_url.rstrip('/')}/search",
            json={
                "api_key": settings.group_search_api_key,
                "query": query,
                "max_results": min(20, max(limit, 10)),
                "include_domains": ["facebook.com"],
            },
        )
    if resp.status_code >= 400:
        raise RuntimeError(f"Tavily {resp.status_code}: {resp.text}")

    groups: list[DiscoveredGroup] = []
    for r in resp.json().get("results", []):
        url = _canonical_group_url(r.get("url", ""))
        if not url:
            continue
        title = (r.get("title") or "Facebook group").replace(" | Facebook", "").strip()
        groups.append(
            DiscoveredGroup(name=title[:300], url=url, snippet=(r.get("content") or "")[:280])
        )
    return _dedupe(groups)[:limit]
