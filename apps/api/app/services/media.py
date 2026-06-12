"""AI video/reel generation: script → storyboard → render → asset, metered by credits.

Flow: business info / product URL / note → LLM writes a UGC-style script +
storyboard → media provider renders (async) → poll → store MediaAsset. Each
render costs credits, deducted from the org and recorded in the ledger.
"""

from __future__ import annotations

import json
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.brand import Brand
from app.models.media import (
    CreditLedger,
    MediaAsset,
    MediaJob,
    MediaJobStatus,
)
from app.models.organization import Organization
from app.services.llm import get_llm_provider
from app.services.llm.base import Message
from app.services.media_provider import RenderBrief, get_media_provider

logger = get_logger(__name__)


class InsufficientCredits(Exception):
    pass


def _script_and_storyboard(brand: Brand, note: str, product_url: str | None) -> tuple[str, list]:
    settings = get_settings()
    subject = note.strip() or product_url or brand.name

    if settings.llm_provider != "mock":
        system = (
            "You are a short-form video scriptwriter. Write a UGC-style, slightly "
            "imperfect 15–20s script. Respond ONLY with JSON: "
            '{"script": str, "storyboard": [{"scene": str, "shot": str}]}.'
        )
        user = f"Brand: {brand.name}\nTopic: {subject}\nProduct URL: {product_url or 'n/a'}"
        result = get_llm_provider().generate(system, [Message(role="user", content=user)])
        try:
            data = json.loads(re.search(r"\{.*\}", result.text, re.DOTALL).group(0))
            return data["script"], data.get("storyboard", [])
        except (AttributeError, KeyError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("media script JSON parse failed, using deterministic: %s", exc)

    script = (
        f"[Hook] You won't believe what {brand.name} just dropped.\n"
        f"[Show] Quick, handheld look at {subject}.\n"
        f"[Value] Here's why people love it.\n"
        f"[CTA] Tap to check it out — link in bio."
    )
    storyboard = [
        {"scene": "Hook", "shot": "Selfie-style talking head, natural light"},
        {"scene": "Product", "shot": f"Close-up b-roll of {subject}"},
        {"scene": "Reaction", "shot": "Genuine reaction, slightly shaky"},
        {"scene": "CTA", "shot": "Text overlay + point to bio"},
    ]
    return script, storyboard


async def _charge_credits(
    session: AsyncSession, org: Organization, amount: int, reason: str
) -> None:
    if org.credit_balance < amount:
        raise InsufficientCredits(
            f"Need {amount} credits, have {org.credit_balance}. Top up to generate."
        )
    org.credit_balance -= amount
    session.add(CreditLedger(org_id=org.id, delta=-amount, reason=reason))


async def generate_video(
    session: AsyncSession,
    *,
    brand: Brand,
    org: Organization,
    note: str,
    product_url: str | None = None,
    style: str = "ugc",
) -> MediaJob:
    settings = get_settings()
    cost = settings.video_cost_credits
    await _charge_credits(session, org, cost, f"video render: {note[:40] or brand.name}")

    script, storyboard = _script_and_storyboard(brand, note, product_url)
    provider = get_media_provider()
    external = provider.start_render(
        RenderBrief(script=script, storyboard=storyboard, product_url=product_url, style=style)
    )

    job = MediaJob(
        brand_id=brand.id,
        provider=provider.name,
        status=MediaJobStatus.rendering,
        prompt=note or (product_url or ""),
        script=script,
        storyboard_json=storyboard,
        external_job_id=external,
        cost_credits=cost,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return job


async def poll_job(session: AsyncSession, job: MediaJob) -> MediaJob:
    """Poll the provider; on completion store the asset and mark the job ready."""
    if job.status != MediaJobStatus.rendering:
        return job
    status = get_media_provider().poll_render(job.external_job_id or "")
    if status.failed:
        job.status = MediaJobStatus.failed
        job.error = "render failed"
    elif status.ready:
        job.status = MediaJobStatus.ready
        job.asset_url = status.asset_url
        session.add(
            MediaAsset(
                brand_id=job.brand_id,
                kind="video",
                url=status.asset_url or "",
                source="ai_generated",
                provider=job.provider,
                media_job_id=job.id,
            )
        )
    await session.commit()
    await session.refresh(job)
    return job


async def poll_rendering_jobs(session: AsyncSession) -> int:
    """Beat helper: advance all rendering jobs."""
    jobs = (
        await session.scalars(
            select(MediaJob).where(MediaJob.status == MediaJobStatus.rendering)
        )
    ).all()
    for job in jobs:
        await poll_job(session, job)
    return len(jobs)


async def add_credits(
    session: AsyncSession, org: Organization, amount: int, reason: str = "top-up"
) -> Organization:
    org.credit_balance += amount
    session.add(CreditLedger(org_id=org.id, delta=amount, reason=reason))
    await session.commit()
    await session.refresh(org)
    return org


async def get_org_for_brand(session: AsyncSession, brand: Brand) -> Organization:
    return await session.get(Organization, brand.org_id)
