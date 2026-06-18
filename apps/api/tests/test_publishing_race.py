"""The scheduled-content poller must claim each due item exactly once, even when
two pollers run concurrently — otherwise a post goes out twice to a real page.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.services.publishing import publish_due_content


async def _brand_with_accounts(client: AsyncClient, headers: dict[str, str]) -> list[str]:
    await client.get("/api/auth/me", headers=headers)
    org = (await client.get("/api/organizations", headers=headers)).json()[0]
    brand_id = (
        await client.post(
            "/api/brands", headers=headers, json={"org_id": org["id"], "name": "Acme"}
        )
    ).json()["id"]
    accts = await client.post(
        "/api/integrations/meta/connect-mock",
        headers=headers,
        json={"brand_id": brand_id, "code": "abc123"},
    )
    return [brand_id, *[a["id"] for a in accts.json()]]


async def test_concurrent_pollers_claim_each_item_once(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    brand_id, *account_ids = await _brand_with_accounts(client, auth_headers)
    past = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()

    # Several due, scheduled items.
    for i in range(5):
        resp = await client.post(
            "/api/content",
            headers=auth_headers,
            json={
                "brand_id": brand_id,
                "body": f"Scheduled #{i}",
                "target_account_ids": account_ids,
                "scheduled_time": past,
            },
        )
        assert resp.json()["status"] == "scheduled"

    async def poll() -> list[str]:
        async with AsyncSessionLocal() as session:
            return [str(i) for i in await publish_due_content(session)]

    a, b = await asyncio.gather(poll(), poll())

    # No item is claimed by both pollers, and all five get published exactly once.
    assert set(a).isdisjoint(set(b)), (a, b)
    assert len(a) + len(b) == 5

    published = await client.get(
        f"/api/content?brand_id={brand_id}&status=published", headers=auth_headers
    )
    assert len(published.json()) == 5
