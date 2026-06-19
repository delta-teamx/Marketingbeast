"""Flagship URL→Presence audit.

Deterministic checks (profile fields, connected platforms, posting cadence)
produce reproducible sub-scores; the LLM adds a qualitative content score, a
strategy brief, and a first-week content plan. Mock mode is deterministic so the
audit runs with no key/network.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.brand import Brand
from app.models.content import ContentItem, ContentStatus
from app.models.social_account import SocialAccount
from app.services.group_finder import detect_niche
from app.services.llm import get_llm_provider
from app.services.llm.base import Message
from app.services.verticals import vertical_profile
from app.services.website import fetch_site_text

logger = get_logger(__name__)


@dataclass
class AuditResult:
    overall_score: int
    overall_grade: str
    sections: list[dict[str, Any]]
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    strategy_brief: str = ""
    content_plan: list[dict[str, Any]] = field(default_factory=list)


def grade_from_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _section(key: str, label: str, score: int, notes: str) -> dict[str, Any]:
    return {"key": key, "label": label, "score": max(0, min(100, score)), "notes": notes}


def build_sections(
    *, brand: Brand, providers: set[str], content_count: int, has_site_text: bool
) -> list[dict[str, Any]]:
    # Profile completeness — deterministic from filled fields.
    fields = [brand.website_url, brand.industry_vertical, brand.niche_summary, brand.logo_url]
    filled = sum(1 for f in fields if f)
    profile = int(((filled + 1) / (len(fields) + 1)) * 100)  # +1 for name (always set)

    breadth = {0: 20, 1: 60}.get(len(providers), 100)
    consistency = 20 if content_count == 0 else 55 if content_count < 4 else 85
    # Without insights yet, engagement is reported as a neutral baseline.
    engagement = 60
    # Content quality leans on the LLM; deterministic baseline in mock mode.
    quality = 72 if has_site_text else 50

    return [
        _section("profile", "Profile completeness", profile, "Based on filled brand fields."),
        _section(
            "breadth", "Platform breadth", breadth, f"{len(providers)} platform(s) connected."
        ),
        _section(
            "consistency", "Posting consistency", consistency, f"{content_count} post(s) on record."
        ),
        _section(
            "engagement", "Engagement health", engagement, "Connect insights for a real score."
        ),
        _section("quality", "Content quality", quality, "Qualitative assessment of your content."),
    ]


def _derive_findings(sections: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    findings: list[str] = []
    recommendations: list[str] = []
    for s in sections:
        if s["score"] < 60:
            findings.append(f"{s['label']} is weak ({s['score']}/100).")
            recommendations.append(_recommendation_for(s["key"]))
    if not findings:
        findings.append("Solid foundation across the board.")
    return findings, recommendations


def _recommendation_for(key: str) -> str:
    return {
        "profile": "Complete your website, industry, and logo so your brand reads as legitimate.",
        "breadth": "Connect both a Facebook Page and an Instagram account to widen reach.",
        "consistency": "Commit to a steady cadence — start with 3–4 posts per week.",
        "engagement": "Connect insights and reply to comments/DMs to lift engagement.",
        "quality": "Use clearer hooks and UGC-style visuals; avoid overly polished ads.",
    }.get(key, "Improve this area.")


async def run_audit(session: AsyncSession, brand: Brand) -> AuditResult:
    settings = get_settings()

    site_text = await fetch_site_text(brand.website_url or "")
    # Ensure we have a niche to anchor the strategy.
    niche = await detect_niche(
        brand_name=brand.name, website_text=site_text, vertical=brand.industry_vertical
    )
    if not brand.niche_summary:
        brand.niche_summary = niche.summary
        brand.niche_keywords = niche.keywords
        if not brand.industry_vertical:
            brand.industry_vertical = niche.category

    providers = set(
        (
            await session.scalars(
                select(SocialAccount.provider).where(SocialAccount.brand_id == brand.id)
            )
        ).all()
    )
    content_count = (
        await session.scalar(
            select(func.count(ContentItem.id)).where(
                ContentItem.brand_id == brand.id,
                ContentItem.status == ContentStatus.published,
            )
        )
    ) or 0

    sections = build_sections(
        brand=brand,
        providers={str(p) for p in providers},
        content_count=content_count,
        has_site_text=bool(site_text),
    )
    overall = round(sum(s["score"] for s in sections) / len(sections))
    findings, recommendations = _derive_findings(sections)

    brief, plan = await _brief_and_plan(
        brand_name=brand.name,
        niche_category=niche.category,
        keywords=niche.keywords,
        mock=settings.llm_provider == "mock",
    )

    return AuditResult(
        overall_score=overall,
        overall_grade=grade_from_score(overall),
        sections=sections,
        findings=findings,
        recommendations=recommendations,
        strategy_brief=brief,
        content_plan=plan,
    )


async def _brief_and_plan(
    *, brand_name: str, niche_category: str, keywords: list[str], mock: bool
) -> tuple[str, list[dict[str, Any]]]:
    if not mock:
        system = (
            "You are a social media strategist. Respond ONLY with JSON: "
            '{"strategy_brief": str, "content_plan": [{"day": str, "idea": str, '
            '"caption": str, "hashtags": [str]}]}. Exactly 7 plan items (one week).'
        )
        user = f"Business: {brand_name}\nNiche: {niche_category}\nKeywords: {', '.join(keywords)}"
        result = get_llm_provider().generate(system, [Message(role="user", content=user)])
        try:
            data = json.loads(re.search(r"\{.*\}", result.text, re.DOTALL).group(0))
            return data["strategy_brief"], data["content_plan"]
        except (AttributeError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("audit plan JSON parse failed, using deterministic plan: %s", exc)

    return _mock_brief_and_plan(brand_name, niche_category, keywords)


def _mock_brief_and_plan(
    brand_name: str, niche_category: str, keywords: list[str]
) -> tuple[str, list[dict[str, Any]]]:
    kw = keywords or [niche_category.lower()]
    profile = vertical_profile(niche_category + " " + " ".join(keywords))
    signature_tag = profile["hashtags"][0]
    offers = profile["offers"]
    brief = (
        f"{brand_name} should sound {profile['voice']} for {profile['audience']} in the "
        f"{niche_category.lower()} space — mixing education, social proof, and soft offers "
        f"(e.g. {offers[0]}). Post 4–5x/week, lead with hooks, and lean on UGC-style visuals."
    )
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    angles = profile["angles"]
    plan = [
        {
            "day": days[i],
            "idea": angles[i % len(angles)],
            "caption": f"{angles[i % len(angles)]} — {brand_name} ({niche_category}).",
            "hashtags": [signature_tag, f"#{kw[0].replace(' ', '')}"],
        }
        for i in range(7)
    ]
    return brief, plan


async def seed_drafts_from_plan(
    session: AsyncSession, *, brand_id: uuid.UUID, plan: list[dict[str, Any]]
) -> list[ContentItem]:
    """Turn a content plan into draft ContentItems (no targets yet) to review."""
    ids: list[uuid.UUID] = []
    for item in plan:
        caption = item.get("caption", "")
        tags = " ".join(item.get("hashtags", []))
        body = f"{caption}\n\n{tags}".strip()
        draft = ContentItem(brand_id=brand_id, body=body, status=ContentStatus.draft)
        session.add(draft)
        await session.flush()
        ids.append(draft.id)
    await session.commit()
    # Re-load with targets eager-loaded for safe serialization.
    rows = (
        await session.scalars(
            select(ContentItem)
            .where(ContentItem.id.in_(ids))
            .options(selectinload(ContentItem.targets))
            .order_by(ContentItem.created_at)
        )
    ).all()
    return list(rows)
