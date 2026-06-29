"""AI Content Engine: brand-voice generation, hashtags, best-times, repurposing.

Generation is brand-voice-aware (niche + voice profile go into the prompt).
Best-times are rules-based for now (upgrade to a per-account model once insight
data exists). Mock mode is deterministic so it runs with no key/network.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.brand import Brand
from app.models.content import ContentItem, ContentStatus, ContentType
from app.services.llm import get_llm_provider
from app.services.llm.base import Message
from app.services.verticals import vertical_profile

logger = get_logger(__name__)

# Rules-based best posting times per weekday (local), pending a learned model.
BEST_TIMES: dict[str, list[str]] = {
    "Mon": ["08:00", "12:00", "18:00"],
    "Tue": ["08:00", "12:00", "19:00"],
    "Wed": ["09:00", "12:00", "18:00"],
    "Thu": ["08:00", "13:00", "19:00"],
    "Fri": ["09:00", "15:00", "17:00"],
    "Sat": ["10:00", "13:00"],
    "Sun": ["11:00", "16:00"],
}


@dataclass
class GeneratedIdea:
    body: str
    content_type: ContentType = ContentType.post
    hashtags: list[str] = field(default_factory=list)
    suggested_time: str = ""


def best_times() -> dict[str, list[str]]:
    return BEST_TIMES


def _voice_hint(brand: Brand) -> str:
    parts = [f"Brand: {brand.name}"]
    if brand.industry_vertical:
        parts.append(f"Industry: {brand.industry_vertical}")
    if brand.niche_summary:
        parts.append(f"Niche: {brand.niche_summary}")
    if brand.niche_keywords:
        parts.append(f"Keywords: {', '.join(brand.niche_keywords)}")
    if brand.voice_profile_json:
        parts.append(f"Voice: {json.dumps(brand.voice_profile_json)}")
    return "\n".join(parts)


async def generate_ideas(brand: Brand, prompt: str, count: int = 7) -> list[GeneratedIdea]:
    settings = get_settings()
    if settings.llm_provider == "mock":
        return _mock_ideas(brand, prompt, count)

    system = (
        "You are a brand's social copywriter. Match the brand voice. Respond ONLY "
        'with a JSON array of {"body", "content_type" (post|reel|story), '
        '"hashtags": [str], "suggested_time"} — exactly N items.'
    )
    user = f"{_voice_hint(brand)}\nIdea/topic: {prompt}\nN = {count}"
    result = await get_llm_provider().agenerate(system, [Message(role="user", content=user)])
    try:
        raw = json.loads(re.search(r"\[.*\]", result.text, re.DOTALL).group(0))
        return [
            GeneratedIdea(
                body=x["body"],
                content_type=ContentType(x.get("content_type", "post")),
                hashtags=x.get("hashtags", []),
                suggested_time=x.get("suggested_time", ""),
            )
            for x in raw[:count]
        ]
    except (AttributeError, KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("content gen JSON parse failed, using deterministic ideas: %s", exc)
        return _mock_ideas(brand, prompt, count)


def _mock_ideas(brand: Brand, prompt: str, count: int) -> list[GeneratedIdea]:
    kw = brand.niche_keywords or [(brand.industry_vertical or "business").lower()]
    days = list(BEST_TIMES.keys())
    profile = vertical_profile(brand.industry_vertical or " ".join(brand.niche_keywords or []))
    angles = profile["angles"]
    signature_tag = profile["hashtags"][0]
    keyword_tag = "#" + (kw[0] if kw else "brand").replace(" ", "")
    ideas: list[GeneratedIdea] = []
    for i in range(count):
        angle = angles[i % len(angles)]
        day = days[i % len(days)]
        ideas.append(
            GeneratedIdea(
                body=f"{angle}: {prompt.strip() or brand.name} — {kw[i % len(kw)]} edition.",
                content_type=ContentType.post,
                hashtags=[signature_tag, keyword_tag],
                suggested_time=BEST_TIMES[day][0],
            )
        )
    return ideas


def repurpose(body: str) -> list[GeneratedIdea]:
    """Turn one idea into post / reel-script / story variants."""
    base = body.strip()
    return [
        GeneratedIdea(body=base, content_type=ContentType.post),
        GeneratedIdea(
            body=(
                f"REEL SCRIPT\nHook: {base[:60]}…\n"
                "Beat 1: show it\nBeat 2: explain\nCTA: follow for more"
            ),
            content_type=ContentType.reel,
        ),
        GeneratedIdea(
            body=f"STORY\n{base[:80]}\n→ swipe up / tap the link",
            content_type=ContentType.story,
        ),
    ]


async def persist_ideas(
    session: AsyncSession, *, brand_id: uuid.UUID, ideas: list[GeneratedIdea]
) -> list[ContentItem]:
    ids: list[uuid.UUID] = []
    for idea in ideas:
        tags = " ".join(idea.hashtags)
        body = f"{idea.body}\n\n{tags}".strip() if tags else idea.body
        item = ContentItem(
            brand_id=brand_id,
            body=body,
            content_type=idea.content_type,
            status=ContentStatus.draft,
            hashtags=idea.hashtags or None,
            suggested_time=idea.suggested_time or None,
        )
        session.add(item)
        await session.flush()
        ids.append(item.id)
    await session.commit()
    rows = (
        await session.scalars(
            select(ContentItem)
            .where(ContentItem.id.in_(ids))
            .options(selectinload(ContentItem.targets))
            .order_by(ContentItem.created_at)
        )
    ).all()
    return list(rows)
