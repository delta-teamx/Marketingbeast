"""Ads service: connect accounts, launch campaigns with 10–20 creative
variations, sync performance, and recommend pause/scale actions.

Creative generation uses the LLM (deterministic in mock mode). The 'launch many
variations to find winners' tactic is the core of this module.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.ads import (
    AdAccount,
    AdCampaign,
    AdCreative,
    CampaignStatus,
    CreativeStatus,
)
from app.models.brand import Brand
from app.services.ads_client import get_ads_client
from app.services.llm import get_llm_provider
from app.services.llm.base import Message

logger = get_logger(__name__)


@dataclass
class CreativeIdea:
    headline: str
    primary_text: str


async def connect_mock_account(session: AsyncSession, brand: Brand) -> AdAccount:
    account = AdAccount(
        brand_id=brand.id,
        external_id=f"act_{uuid.uuid4().hex[:12]}",
        name=f"{brand.name} Ad Account",
        status="connected",
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return account


def generate_creatives(brand: Brand, concept: str, count: int = 12) -> list[CreativeIdea]:
    """Produce N ad creative variations for one concept."""
    settings = get_settings()
    count = max(1, min(count, 20))

    if settings.llm_provider == "mock":
        return _mock_creatives(brand, concept, count)

    system = (
        "You are a performance ad copywriter. Produce N distinct ad variations. "
        'Respond ONLY with a JSON array of {"headline", "primary_text"}.'
    )
    user = f"Brand: {brand.name}\nConcept: {concept}\nN = {count}"
    result = get_llm_provider().generate(system, [Message(role="user", content=user)])
    try:
        raw = json.loads(re.search(r"\[.*\]", result.text, re.DOTALL).group(0))
        ideas = [CreativeIdea(x["headline"], x.get("primary_text", "")) for x in raw[:count]]
        if ideas:
            return ideas
    except (AttributeError, KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("ad creative JSON parse failed, using deterministic set: %s", exc)
    return _mock_creatives(brand, concept, count)


def _mock_creatives(brand: Brand, concept: str, count: int) -> list[CreativeIdea]:
    hooks = [
        "Stop scrolling —", "New:", "Limited time:", "Locals love this:",
        "Tired of the old way?", "The secret to", "Don't miss out on",
        "Your search ends here:", "Why everyone's switching to", "Save big on",
        "Finally, a better", "Ready for", "Meet your new favorite", "Just dropped:",
        "Last chance:", "Hot deal:", "Upgrade your", "Trusted by hundreds:",
        "Book today —", "Get more from",
    ]
    base = concept.strip() or f"{brand.name}"
    return [
        CreativeIdea(
            headline=f"{hooks[i % len(hooks)]} {base}"[:120],
            primary_text=(
                f"{brand.name} makes {base.lower()} easy. "
                f"Tap to learn more and get started today. (v{i + 1})"
            ),
        )
        for i in range(count)
    ]


async def launch_campaign(
    session: AsyncSession,
    *,
    brand: Brand,
    ad_account: AdAccount,
    name: str,
    objective: str,
    daily_budget: float,
    concept: str,
    n_variations: int = 12,
) -> AdCampaign:
    client = get_ads_client()
    ext = client.create_campaign(
        account_external_id=ad_account.external_id, name=name, objective=objective
    )
    campaign = AdCampaign(
        brand_id=brand.id,
        ad_account_id=ad_account.id,
        external_id=ext,
        name=name,
        objective=objective,
        daily_budget=daily_budget,
        status=CampaignStatus.active,
    )
    session.add(campaign)
    await session.flush()

    for i, idea in enumerate(generate_creatives(brand, concept, n_variations)):
        creative_ext = client.create_creative(campaign_external_id=ext, headline=idea.headline)
        session.add(
            AdCreative(
                campaign_id=campaign.id,
                external_id=creative_ext,
                variation_index=i,
                headline=idea.headline,
                primary_text=idea.primary_text,
            )
        )
    await session.commit()
    return await load_campaign(session, campaign.id)


async def load_campaign(session: AsyncSession, campaign_id: uuid.UUID) -> AdCampaign | None:
    return await session.scalar(
        select(AdCampaign)
        .where(AdCampaign.id == campaign_id)
        .options(selectinload(AdCampaign.creatives))
        .execution_options(populate_existing=True)
    )


async def sync_campaign_insights(session: AsyncSession, campaign: AdCampaign) -> AdCampaign:
    client = get_ads_client()
    totals = {"impressions": 0, "clicks": 0, "spend": 0.0, "conversions": 0}
    for creative in campaign.creatives:
        m = client.fetch_insights(external_id=creative.external_id or str(creative.id))
        creative.metrics_json = m.as_dict()
        totals["impressions"] += m.impressions
        totals["clicks"] += m.clicks
        totals["spend"] += m.spend
        totals["conversions"] += m.conversions
    totals["spend"] = round(totals["spend"], 2)
    totals["ctr"] = (
        round(totals["clicks"] / totals["impressions"] * 100, 2)
        if totals["impressions"]
        else 0.0
    )
    campaign.metrics_json = totals
    await session.commit()
    return await load_campaign(session, campaign.id)


def recommendations(campaign: AdCampaign) -> dict:
    """Recommend pausing low-CTR creatives and scaling winners."""
    scored = [
        (c, float(c.metrics_json.get("ctr", 0.0)))
        for c in campaign.creatives
        if c.metrics_json
    ]
    if not scored:
        return {"recommendations": [], "summary": "Sync insights to get recommendations."}

    ctrs = [ctr for _, ctr in scored]
    avg = sum(ctrs) / len(ctrs)
    recs = []
    for creative, ctr in sorted(scored, key=lambda x: x[1], reverse=True):
        if ctr >= avg * 1.3:
            recs.append({"creative_id": str(creative.id), "action": "scale",
                         "reason": f"CTR {ctr}% beats the {avg:.2f}% average — scale budget."})
        elif ctr < avg * 0.6:
            recs.append({"creative_id": str(creative.id), "action": "pause",
                         "reason": f"CTR {ctr}% trails the {avg:.2f}% average — pause it."})
    winners = sum(1 for r in recs if r["action"] == "scale")
    losers = sum(1 for r in recs if r["action"] == "pause")
    summary = (
        f"Found {winners} winner(s) to scale and {losers} underperformer(s) to pause. "
        f"Average CTR is {avg:.2f}%."
    )
    return {"recommendations": recs, "summary": summary}


async def set_campaign_status(
    session: AsyncSession, campaign: AdCampaign, status: CampaignStatus
) -> AdCampaign:
    campaign.status = status
    await session.commit()
    return await load_campaign(session, campaign.id)


async def set_creative_status(
    session: AsyncSession, creative: AdCreative, status: CreativeStatus
) -> AdCreative:
    creative.status = status
    await session.commit()
    await session.refresh(creative)
    return creative
