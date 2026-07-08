"""Niche detection + AI Facebook-group suggestions for lead generation.

Compliance: there is no Meta API to query real groups, so these are *advisory*
AI suggestions (group name + the keyword to search on Facebook + scores +
rationale). The user joins manually; posting happens only via the Tier B
extension. The backend never touches Facebook groups.

Mock mode (LLM_PROVIDER=mock, the default) produces deterministic output so dev
and tests run with no network and no API key — mirroring META_MODE=mock. Live
mode prompts Claude for strict JSON, validated with Pydantic.
"""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, ValidationError

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.group_discovery import DiscoveredGroup, discover_groups
from app.services.llm import get_llm_provider
from app.services.llm.base import Message

logger = get_logger(__name__)

_STOPWORDS = {
    "the", "and", "for", "with", "your", "you", "our", "are", "from", "that",
    "this", "have", "all", "get", "more", "best", "home", "about", "contact",
}


class NicheProfile(BaseModel):
    category: str
    summary: str
    keywords: list[str] = Field(default_factory=list)


class GroupSuggestionData(BaseModel):
    name: str
    search_keyword: str
    # Set only for REAL groups found via web-search discovery.
    group_url: str | None = None
    estimated_size: str = "unknown"
    relevance_score: int = Field(ge=0, le=100)
    lead_quality_score: int = Field(ge=0, le=100)
    rationale: str = ""
    suggested_post_angle: str = ""


def _keywords_from_text(text: str, brand_name: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]{4,}", f"{brand_name} {text}".lower())
    seen: list[str] = []
    for w in words:
        if w not in _STOPWORDS and w not in seen:
            seen.append(w)
        if len(seen) >= 6:
            break
    return seen or ["local", "business"]


async def detect_niche(*, brand_name: str, website_text: str, vertical: str | None) -> NicheProfile:
    """Classify a brand's niche from its website text (LLM in live mode)."""
    settings = get_settings()
    keywords = _keywords_from_text(website_text, brand_name)

    if settings.llm_provider == "mock" or not website_text:
        category = vertical or (keywords[0].title() if keywords else "General")
        return NicheProfile(
            category=category,
            summary=f"{brand_name} operates in the {category.lower()} space.",
            keywords=keywords,
        )

    system = (
        "You classify a business's marketing niche. Respond ONLY with JSON: "
        '{"category": str, "summary": str, "keywords": [str, ...]}.'
    )
    user = (
        f"Business name: {brand_name}\nVertical: {vertical or 'unknown'}\n"
        f"Website text:\n{website_text}"
    )
    result = await get_llm_provider().agenerate(system, [Message(role="user", content=user)])
    try:
        return NicheProfile.model_validate(_extract_json(result.text))
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("niche JSON parse failed, falling back: %s", exc)
        return NicheProfile(category=vertical or "General", summary="", keywords=keywords)


def _rank_discovered(
    brand_name: str, niche: NicheProfile, discovered: list[DiscoveredGroup]
) -> list[GroupSuggestionData]:
    """Turn REAL discovered groups into ranked suggestions (heuristic scores by
    result order — the groups are verified to exist, which is the key part)."""
    keyword = niche.keywords[0] if niche.keywords else niche.category.lower()
    out: list[GroupSuggestionData] = []
    for i, g in enumerate(discovered):
        relevance = max(60, 95 - i * 4)
        out.append(
            GroupSuggestionData(
                name=g.name,
                search_keyword=keyword,
                group_url=g.url,
                estimated_size="unknown",
                relevance_score=relevance,
                lead_quality_score=max(50, relevance - 8),
                rationale=(
                    g.snippet
                    or f"Real Facebook group relevant to {niche.category} — found via web search."
                ),
                suggested_post_angle=(
                    f"Share a helpful {niche.category.lower()} tip, then introduce "
                    f"{brand_name} and invite a conversation."
                ),
            )
        )
    return out


async def suggest_groups(*, brand_name: str, niche: NicheProfile) -> list[GroupSuggestionData]:
    """Produce ranked Facebook-group suggestions for lead gen.

    Prefers REAL groups discovered via web search (GROUP_SEARCH_PROVIDER); falls
    back to AI-advisory suggestions when discovery is off or finds nothing."""
    settings = get_settings()

    try:
        discovered = await discover_groups(category=niche.category, keywords=niche.keywords)
    except Exception as exc:  # noqa: BLE001 - discovery is best-effort
        logger.warning("group discovery failed, using advisory suggestions: %s", exc)
        discovered = []
    if discovered:
        return _rank_discovered(brand_name, niche, discovered)

    if settings.llm_provider == "mock":
        return _mock_suggestions(brand_name, niche)

    system = (
        "You suggest Facebook Groups a business should join to find leads. "
        "Respond ONLY with a JSON array of objects: "
        '{"name", "search_keyword", "estimated_size", "relevance_score" (0-100), '
        '"lead_quality_score" (0-100), "rationale", "suggested_post_angle"}. '
        "Prefer active, buyer-intent communities; avoid spammy promo groups."
    )
    user = f"Business: {brand_name}\nNiche: {niche.category}\nKeywords: {', '.join(niche.keywords)}"
    result = await get_llm_provider().agenerate(system, [Message(role="user", content=user)])
    try:
        raw = _extract_json(result.text)
        items = [GroupSuggestionData.model_validate(x) for x in raw]
        return sorted(items, key=lambda s: s.relevance_score, reverse=True)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("group JSON parse failed, falling back: %s", exc)
        return _mock_suggestions(brand_name, niche)


def _mock_suggestions(brand_name: str, niche: NicheProfile) -> list[GroupSuggestionData]:
    cat = niche.category
    kw = niche.keywords or [cat.lower()]
    templates = [
        ("{cat} Enthusiasts & Buyers", f"{cat} buyers", "large", 92, 80,
         f"Highly active community discussing {cat.lower()} purchases — strong buyer intent.",
         f"Share a helpful {cat.lower()} tip, then mention {brand_name} softly."),
        (f"Local {cat} Community", f"local {kw[0]}", "medium", 85, 88,
         "Local members ask for recommendations — ideal for nearby leads.",
         "Answer a member's question and offer a free consult."),
        (f"{cat} Deals & Recommendations", f"{kw[0]} recommendations", "large", 78, 72,
         "Members actively seek vendor recommendations.",
         "Post a limited-time offer with a clear call to action."),
        (f"{kw[-1].title()} Owners Group", f"{kw[-1]} owners", "medium", 70, 75,
         "Owners share problems your product solves.",
         "Lead with a how-to, then link your guide."),
    ]
    return [
        GroupSuggestionData(
            name=n.format(cat=cat),
            search_keyword=k,
            estimated_size=size,
            relevance_score=rel,
            lead_quality_score=lead,
            rationale=why,
            suggested_post_angle=angle,
        )
        for (n, k, size, rel, lead, why, angle) in templates
    ]


def _extract_json(text: str) -> object:
    """Pull the first JSON object/array out of an LLM response."""
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if not match:
        raise ValueError("no JSON found in LLM response")
    return json.loads(match.group(1))
