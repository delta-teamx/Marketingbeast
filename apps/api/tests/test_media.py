"""DB-backed media smoke: credits → generate → poll → asset; insufficient credits."""

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


async def test_generate_and_poll(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _brand(client, auth_headers)

    credits = await client.get(f"/api/brands/{brand_id}/credits", headers=auth_headers)
    start = credits.json()["credit_balance"]
    assert start >= 100  # starter credits

    gen = await client.post(
        f"/api/brands/{brand_id}/videos/generate",
        headers=auth_headers,
        json={"note": "fall menu reel"},
    )
    assert gen.status_code == 201
    job = gen.json()
    assert job["status"] == "rendering"
    assert job["script"]
    assert len(job["storyboard_json"]) >= 1
    assert job["cost_credits"] == 10

    # Credits were deducted.
    after = (await client.get(f"/api/brands/{brand_id}/credits", headers=auth_headers)).json()
    assert after["credit_balance"] == start - 10

    # Poll → ready + asset created.
    polled = await client.post(f"/api/media-jobs/{job['id']}/poll", headers=auth_headers)
    assert polled.json()["status"] == "ready"
    assert polled.json()["asset_url"]

    assets = await client.get(f"/api/brands/{brand_id}/media-assets", headers=auth_headers)
    assert len(assets.json()) == 1
    assert assets.json()[0]["source"] == "ai_generated"


async def test_insufficient_credits(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _brand(client, auth_headers)
    # Starter credits = 100, each video = 10 → 10 succeed, 11th fails with 402.
    for _ in range(10):
        r = await client.post(
            f"/api/brands/{brand_id}/videos/generate",
            headers=auth_headers,
            json={"note": "clip"},
        )
        assert r.status_code == 201
    blocked = await client.post(
        f"/api/brands/{brand_id}/videos/generate", headers=auth_headers, json={"note": "clip"}
    )
    assert blocked.status_code == 402

    # Top up and it works again.
    await client.post(
        f"/api/brands/{brand_id}/credits/topup", headers=auth_headers, json={"amount": 50}
    )
    ok = await client.post(
        f"/api/brands/{brand_id}/videos/generate", headers=auth_headers, json={"note": "clip"}
    )
    assert ok.status_code == 201
