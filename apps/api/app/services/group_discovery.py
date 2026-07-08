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


def _extract_group_urls(text: str) -> list[str]:
    """All canonical Facebook group URLs mentioned in a blob of text, in order."""
    out: list[str] = []
    seen: set[str] = set()
    for m in _GROUP_URL_RE.finditer(text or ""):
        url = _canonical_group_url(m.group(0))
        if url and url not in seen:
            seen.add(url)
            out.append(url)
    return out


def _name_from_url(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1]
    if slug.isdigit():
        return "Facebook group"
    return slug.replace("-", " ").replace(".", " ").replace("_", " ").title()


async def discover_groups(*, queries: list[str], limit: int = 12) -> list[DiscoveredGroup]:
    """Discover REAL Facebook groups for a set of lead-focused search queries.

    Returns [] when the feature is off (GROUP_SEARCH_PROVIDER=none). Group links are
    extracted both from result URLs and from result content (e.g. 'best FB groups
    for X' round-ups), since Facebook itself is largely uncrawlable."""
    provider = get_settings().group_search_provider
    if provider in ("", "none") or not queries:
        return []
    if provider == "tavily":
        return await _tavily(queries, limit)
    logger.warning("unknown GROUP_SEARCH_PROVIDER=%s; skipping discovery", provider)
    return []


async def _tavily(queries: list[str], limit: int) -> list[DiscoveredGroup]:
    settings = get_settings()
    if not settings.group_search_api_key:
        raise RuntimeError("GROUP_SEARCH_API_KEY is required for the tavily group search provider")
    base = settings.group_search_base_url.rstrip("/")
    groups: list[DiscoveredGroup] = []
    seen: set[str] = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for query in queries[:6]:
            try:
                resp = await client.post(
                    f"{base}/search",
                    json={
                        "api_key": settings.group_search_api_key,
                        "query": query,
                        "max_results": 6,
                        "search_depth": "advanced",
                        "include_raw_content": True,
                    },
                )
            except httpx.HTTPError as exc:
                logger.warning("tavily query failed (%s): %s", query, exc)
                continue
            if resp.status_code >= 400:
                logger.warning("tavily %s: %s", resp.status_code, resp.text[:200])
                continue

            for r in resp.json().get("results", []):
                result_url = r.get("url", "")
                result_group = _canonical_group_url(result_url)
                title = (r.get("title") or "").replace(" | Facebook", "").strip()
                blob = f"{result_url}\n{r.get('content', '')}\n{r.get('raw_content') or ''}"
                for url in _extract_group_urls(blob):
                    if url in seen:
                        continue
                    seen.add(url)
                    name = title if (result_group == url and title) else _name_from_url(url)
                    groups.append(
                        DiscoveredGroup(
                            name=name[:300], url=url, snippet=(r.get("content") or "")[:280]
                        )
                    )
                    if len(groups) >= limit:
                        return groups
    return groups
