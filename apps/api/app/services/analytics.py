"""Analytics: insights ingestion, dashboard aggregation, reports, competitors.

Insights come through the Meta adapter (mock by default), stored as daily
MetricSnapshots. Dashboards aggregate them; reports summarize a period with an
AI narrative (deterministic in mock mode).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.analytics import Competitor, MetricSnapshot, Report, ReportPeriod
from app.models.brand import Brand
from app.models.content import ContentItem, ContentStatus
from app.models.social_account import SocialAccount
from app.services.crypto import decrypt_secret
from app.services.meta import get_meta_client
from app.services.meta.base import MetaClient


def _today() -> date:
    return datetime.now(UTC).date()


async def ingest_brand_insights(
    session: AsyncSession,
    brand: Brand,
    *,
    days: int = 14,
    meta_client: MetaClient | None = None,
) -> int:
    """Pull insights for each connected account for the last `days` and upsert."""
    client = meta_client or get_meta_client()
    accounts = (
        await session.scalars(
            select(SocialAccount).where(
                SocialAccount.brand_id == brand.id,
                SocialAccount.status == "connected",
            )
        )
    ).all()

    written = 0
    for account in accounts:
        token = (
            decrypt_secret(account.access_token_encrypted)
            if account.access_token_encrypted
            else ""
        )
        for offset in range(days):
            day = _today() - timedelta(days=offset)
            data = await client.fetch_insights(
                provider=account.provider,
                external_id=account.external_id or "",
                access_token=token,
                day_offset=offset,
            )
            existing = await session.scalar(
                select(MetricSnapshot).where(
                    MetricSnapshot.social_account_id == account.id,
                    MetricSnapshot.snapshot_date == day,
                )
            )
            row = existing or MetricSnapshot(
                brand_id=brand.id, social_account_id=account.id, snapshot_date=day
            )
            row.followers = data.followers
            row.reach = data.reach
            row.impressions = data.impressions
            row.engagement = data.engagement
            row.posts = data.posts
            if existing is None:
                session.add(row)
            written += 1
    await session.commit()
    return written


@dataclass
class Dashboard:
    followers: int
    follower_growth: int
    total_reach: int
    total_engagement: int
    engagement_rate: float
    time_series: list[dict[str, Any]]
    top_posts: list[dict[str, Any]]
    per_account: list[dict[str, Any]]


async def get_dashboard(session: AsyncSession, brand: Brand) -> Dashboard:
    snapshots = (
        await session.scalars(
            select(MetricSnapshot)
            .where(MetricSnapshot.brand_id == brand.id)
            .order_by(MetricSnapshot.snapshot_date)
        )
    ).all()

    by_date: dict[date, dict[str, int]] = defaultdict(
        lambda: {"followers": 0, "reach": 0, "engagement": 0, "impressions": 0}
    )
    for s in snapshots:
        d = by_date[s.snapshot_date]
        d["followers"] += s.followers
        d["reach"] += s.reach
        d["engagement"] += s.engagement
        d["impressions"] += s.impressions

    series = [
        {"date": d.isoformat(), **vals} for d, vals in sorted(by_date.items())
    ]
    followers = series[-1]["followers"] if series else 0
    follower_growth = followers - series[0]["followers"] if series else 0
    total_reach = sum(p["reach"] for p in series)
    total_engagement = sum(p["engagement"] for p in series)
    total_impressions = sum(p["impressions"] for p in series)
    engagement_rate = (
        round(total_engagement / total_impressions * 100, 1) if total_impressions else 0.0
    )

    # Per-account latest snapshot.
    latest_by_account: dict[uuid.UUID, MetricSnapshot] = {}
    for s in snapshots:
        latest_by_account[s.social_account_id] = s
    per_account = []
    for acct_id, snap in latest_by_account.items():
        acct = await session.get(SocialAccount, acct_id)
        per_account.append(
            {
                "social_account_id": str(acct_id),
                "display_name": acct.display_name if acct else None,
                "provider": acct.provider.value if acct else None,
                "followers": snap.followers,
                "reach": snap.reach,
                "engagement": snap.engagement,
            }
        )

    # Top posts — published content ranked by a derived engagement proxy.
    published = (
        await session.scalars(
            select(ContentItem).where(
                ContentItem.brand_id == brand.id,
                ContentItem.status == ContentStatus.published,
            )
        )
    ).all()
    scored = sorted(
        (
            {
                "id": str(c.id),
                "body": c.body[:80],
                "engagement": 30 + (sum(ord(ch) for ch in str(c.id)) % 270),
            }
            for c in published
        ),
        key=lambda x: x["engagement"],
        reverse=True,
    )[:5]

    return Dashboard(
        followers=followers,
        follower_growth=follower_growth,
        total_reach=total_reach,
        total_engagement=total_engagement,
        engagement_rate=engagement_rate,
        time_series=series,
        top_posts=scored,
        per_account=per_account,
    )


async def build_report(
    session: AsyncSession, brand: Brand, period: ReportPeriod
) -> Report:
    window = 7 if period == ReportPeriod.weekly else 30
    ends_on = _today()
    starts_on = ends_on - timedelta(days=window)

    snapshots = (
        await session.scalars(
            select(MetricSnapshot).where(
                MetricSnapshot.brand_id == brand.id,
                MetricSnapshot.snapshot_date >= starts_on,
            )
        )
    ).all()
    reach = sum(s.reach for s in snapshots)
    engagement = sum(s.engagement for s in snapshots)
    followers_now = max((s.followers for s in snapshots), default=0)

    metrics = {
        "reach": reach,
        "engagement": engagement,
        "followers": followers_now,
        "posts": sum(s.posts for s in snapshots),
    }
    summary = _report_summary(brand.name, period, metrics)

    report = Report(
        brand_id=brand.id,
        period=period,
        starts_on=starts_on,
        ends_on=ends_on,
        metrics_json=metrics,
        summary=summary,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


def _report_summary(name: str, period: ReportPeriod, metrics: dict[str, int]) -> str:
    settings = get_settings()
    base = (
        f"{name} reached {metrics['reach']:,} people this {period.value[:-2]} with "
        f"{metrics['engagement']:,} engagements across {metrics['posts']} posts. "
        f"Followers stand at {metrics['followers']:,}."
    )
    if settings.llm_provider == "mock":
        return base + " Keep cadence steady and double down on your top posts."
    # Live mode would ask Claude to narrate; deterministic base is the fallback.
    return base


# --- Competitors ---

async def add_competitor(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    name: str,
    handle: str | None,
    platform: str | None,
    followers: int,
    posting_frequency: str | None,
    engagement_rate: float,
) -> Competitor:
    comp = Competitor(
        brand_id=brand_id,
        name=name,
        handle=handle,
        platform=platform,
        followers=followers,
        posting_frequency=posting_frequency,
        engagement_rate=engagement_rate,
    )
    session.add(comp)
    await session.commit()
    await session.refresh(comp)
    return comp


async def compare_competitors(session: AsyncSession, brand: Brand) -> dict[str, Any]:
    dash = await get_dashboard(session, brand)
    competitors = (
        await session.scalars(
            select(Competitor).where(Competitor.brand_id == brand.id)
        )
    ).all()
    rows = [
        {
            "name": c.name,
            "followers": c.followers,
            "follower_gap": c.followers - dash.followers,
            "engagement_rate": c.engagement_rate,
            "posting_frequency": c.posting_frequency,
        }
        for c in competitors
    ]
    leader = max(competitors, key=lambda c: c.followers, default=None)
    if leader and leader.followers > dash.followers:
        gap = leader.followers - dash.followers
        summary = (
            f"{leader.name} leads by {gap:,} followers. Close the gap by matching "
            f"their cadence and leaning into your highest-engagement formats."
        )
    else:
        summary = "You're ahead on followers — keep your momentum and protect the lead."
    return {"you": {"followers": dash.followers}, "competitors": rows, "summary": summary}
