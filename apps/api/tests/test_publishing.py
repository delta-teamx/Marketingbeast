"""DB-backed Phase 1 smoke: connect (mock) → create → publish, end to end."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient


async def _make_brand(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)  # provision personal org
    org = (await client.get("/api/organizations", headers=headers)).json()[0]
    brand = await client.post(
        "/api/brands", headers=headers, json={"org_id": org["id"], "name": "Acme Coffee"}
    )
    return brand.json()["id"]


async def _connect(client: AsyncClient, headers: dict[str, str], brand_id: str) -> list[str]:
    resp = await client.post(
        "/api/integrations/meta/connect-mock",
        headers=headers,
        json={"brand_id": brand_id, "code": "abc123"},
    )
    assert resp.status_code == 200
    return [a["id"] for a in resp.json()]


async def test_connect_create_publish(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _make_brand(client, auth_headers)
    account_ids = await _connect(client, auth_headers, brand_id)
    assert len(account_ids) == 2

    accounts = await client.get(
        f"/api/social-accounts?brand_id={brand_id}", headers=auth_headers
    )
    assert all(a["status"] == "connected" for a in accounts.json())

    created = await client.post(
        "/api/content",
        headers=auth_headers,
        json={
            "brand_id": brand_id,
            "body": "Fresh roast today ☕",
            "target_account_ids": account_ids,
        },
    )
    assert created.status_code == 201
    item = created.json()
    assert item["status"] == "draft"
    assert len(item["targets"]) == 2

    published = await client.post(
        f"/api/content/{item['id']}/publish", headers=auth_headers
    )
    assert published.status_code == 200
    pub = published.json()
    assert pub["status"] == "published"
    post_ids = [t["external_post_id"] for t in pub["targets"]]
    assert all(pid is not None for pid in post_ids)

    # Idempotent: publishing again keeps the same external post ids (no double-post).
    again = await client.post(f"/api/content/{item['id']}/publish", headers=auth_headers)
    again_ids = [t["external_post_id"] for t in again.json()["targets"]]
    assert sorted(again_ids) == sorted(post_ids)


async def test_scheduled_due_publishing(
    client: AsyncClient, auth_headers: dict[str, str], db
) -> None:
    from app.services.publishing import publish_due_content

    brand_id = await _make_brand(client, auth_headers)
    account_ids = await _connect(client, auth_headers, brand_id)

    past = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    created = await client.post(
        "/api/content",
        headers=auth_headers,
        json={
            "brand_id": brand_id,
            "body": "Scheduled post",
            "target_account_ids": account_ids,
            "scheduled_time": past,
        },
    )
    assert created.json()["status"] == "scheduled"

    # The beat poller publishes everything that is due.
    published_ids = await publish_due_content(db)
    assert len(published_ids) == 1

    listing = await client.get(
        f"/api/content?brand_id={brand_id}&status=published", headers=auth_headers
    )
    assert len(listing.json()) == 1
