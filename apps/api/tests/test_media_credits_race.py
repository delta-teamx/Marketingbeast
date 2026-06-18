"""Credits must never oversell: concurrent renders for the same org can spend at
most the available balance — no free video, no negative balance.
"""

from __future__ import annotations

import asyncio
import uuid

from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.brand import Brand
from app.models.media import MediaJob
from app.models.organization import Organization
from app.services.media import InsufficientCredits, generate_video, get_org_for_brand


async def test_concurrent_renders_cannot_overspend(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    await client.get("/api/auth/me", headers=auth_headers)
    org = (await client.get("/api/organizations", headers=auth_headers)).json()[0]
    org_id = uuid.UUID(org["id"])
    brand_id = uuid.UUID(
        (
            await client.post(
                "/api/brands", headers=auth_headers, json={"org_id": org["id"], "name": "Acme"}
            )
        ).json()["id"]
    )

    # Pin the balance to exactly one render's worth of credits.
    async with AsyncSessionLocal() as s:
        o = await s.get(Organization, org_id)
        o.credit_balance = 10  # == settings.video_cost_credits
        await s.commit()

    async def render() -> bool:
        async with AsyncSessionLocal() as session:
            brand = await session.get(Brand, brand_id)
            o = await get_org_for_brand(session, brand)
            try:
                await generate_video(session, brand=brand, org=o, note="reel")
                return True
            except InsufficientCredits:
                return False

    results = await asyncio.gather(*[render() for _ in range(5)])

    # Exactly one render should have succeeded; the rest hit InsufficientCredits.
    assert sum(results) == 1, results

    async with AsyncSessionLocal() as session:
        bal = await session.scalar(
            select(Organization.credit_balance).where(Organization.id == org_id)
        )
        jobs = (
            await session.scalars(select(MediaJob).where(MediaJob.brand_id == brand_id))
        ).all()
    assert bal == 0
    assert len(jobs) == 1
