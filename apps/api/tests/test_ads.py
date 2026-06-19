"""DB-backed ads smoke: connect account → launch campaign → sync → recommend."""

from __future__ import annotations

from httpx import AsyncClient


async def _brand(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)
    org = (await client.get("/api/organizations", headers=headers)).json()[0]
    return (
        await client.post(
            "/api/brands", headers=headers, json={"org_id": org["id"], "name": "Acme Coffee"}
        )
    ).json()["id"]


async def test_launch_sync_recommend(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _brand(client, auth_headers)

    account = await client.post(
        f"/api/brands/{brand_id}/ad-accounts/connect-mock", headers=auth_headers
    )
    assert account.status_code == 200
    account_id = account.json()["id"]

    created = await client.post(
        f"/api/brands/{brand_id}/campaigns",
        headers=auth_headers,
        json={
            "ad_account_id": account_id,
            "name": "Fall Promo",
            "objective": "LEADS",
            "daily_budget": 25,
            "concept": "fall menu launch",
            "n_variations": 12,
        },
    )
    assert created.status_code == 201
    campaign = created.json()
    assert campaign["status"] == "active"
    assert len(campaign["creatives"]) == 12

    # Before syncing, recommendations need data.
    rec0 = await client.get(
        f"/api/campaigns/{campaign['id']}/recommendations", headers=auth_headers
    )
    assert rec0.json()["recommendations"] == []

    synced = await client.post(
        f"/api/campaigns/{campaign['id']}/sync", headers=auth_headers
    )
    assert synced.status_code == 200
    assert synced.json()["metrics_json"]["impressions"] > 0
    assert all(c["metrics_json"].get("ctr") is not None for c in synced.json()["creatives"])

    rec = await client.get(
        f"/api/campaigns/{campaign['id']}/recommendations", headers=auth_headers
    )
    assert rec.json()["summary"]

    # Pause the campaign.
    paused = await client.patch(
        f"/api/campaigns/{campaign['id']}/status",
        headers=auth_headers,
        json={"status": "paused"},
    )
    assert paused.json()["status"] == "paused"

    listing = await client.get(f"/api/brands/{brand_id}/campaigns", headers=auth_headers)
    assert len(listing.json()) == 1
