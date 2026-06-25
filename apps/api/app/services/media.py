"""AI video/reel generation: script → storyboard → render → asset, metered by credits.

Flow: business info / product URL / note → LLM writes a UGC-style script +
storyboard → media provider renders (async) → poll → store MediaAsset. Each
render costs credits, deducted from the org and recorded in the ledger.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime

from sqlalchemy import select, update
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


class RenderStartError(Exception):
    """The media provider failed to start a render (charged credits are refunded)."""

    pass


async def _script_and_storyboard(
    brand: Brand, note: str, product_url: str | None
) -> tuple[str, list]:
    settings = get_settings()
    subject = note.strip() or product_url or brand.name

    if settings.llm_provider != "mock":
        system = (
            "You are a short-form video scriptwriter. Write a UGC-style, slightly "
            "imperfect 15–20s script. Respond ONLY with JSON: "
            '{"script": str, "storyboard": [{"scene": str, "shot": str}]}.'
        )
        user = f"Brand: {brand.name}\nTopic: {subject}\nProduct URL: {product_url or 'n/a'}"
        result = await get_llm_provider().agenerate(system, [Message(role="user", content=user)])
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
    # Atomic conditional decrement: the WHERE guards the balance under a row
    # lock, so two concurrent renders for the same org can't both pass a stale
    # check and overspend (no free credits / negative balance).
    result = await session.execute(
        update(Organization)
        .where(Organization.id == org.id, Organization.credit_balance >= amount)
        .values(credit_balance=Organization.credit_balance - amount)
    )
    if result.rowcount == 0:
        raise InsufficientCredits(
            f"Need {amount} credits, have {org.credit_balance}. Top up to generate."
        )
    session.add(CreditLedger(org_id=org.id, delta=-amount, reason=reason))
    # Keep the in-memory org consistent with the committed decrement.
    await session.refresh(org)


async def _refund_credits(
    session: AsyncSession, org: Organization, amount: int, reason: str
) -> None:
    """Reverse a prior decrement (e.g. when the render never started)."""
    await session.execute(
        update(Organization)
        .where(Organization.id == org.id)
        .values(credit_balance=Organization.credit_balance + amount)
    )
    session.add(CreditLedger(org_id=org.id, delta=amount, reason=reason))
    await session.refresh(org)


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

    script, storyboard = await _script_and_storyboard(brand, note, product_url)
    provider = get_media_provider()
    try:
        external = provider.start_render(
            RenderBrief(script=script, storyboard=storyboard, product_url=product_url, style=style)
        )
    except Exception as exc:
        # The render never started — refund the credits we just charged so the
        # user isn't billed for nothing, and surface a clean error (not a 500).
        await _refund_credits(session, org, cost, f"refund: render failed to start ({brand.name})")
        await session.commit()
        logger.warning("media render failed to start, refunded %d credits: %s", cost, exc)
        raise RenderStartError(str(exc)) from exc

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


async def publish_media_asset(
    session: AsyncSession,
    *,
    asset: MediaAsset,
    body: str,
    target_account_ids: list[uuid.UUID],
    scheduled_time: datetime | None = None,
):
    """Turn a generated MediaAsset into a reel ContentItem and publish/schedule it.

    Publishes immediately when no `scheduled_time` is given; otherwise leaves the
    item scheduled for the due-poller. Returns the resulting ContentItem.
    """
    # Imported here to avoid a circular import (publishing → media services).
    from app.models.content import ContentType
    from app.services.publishing import create_content_item, publish_content_item

    item = await create_content_item(
        session,
        brand_id=asset.brand_id,
        body=body,
        content_type=ContentType.reel,
        media_urls=[asset.url],
        target_account_ids=target_account_ids,
        scheduled_time=scheduled_time,
    )
    if scheduled_time is None:
        return await publish_content_item(session, item.id)
    return item
