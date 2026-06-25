"""Generate a reel and publish it end to end via the mock (no network/creds)."""

from __future__ import annotations

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


async def test_generate_and_publish_reel(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    brand_id = await _make_brand(client, auth_headers)
    account_ids = await _connect(client, auth_headers, brand_id)
    assert len(account_ids) == 2

    # Generate a video (new orgs get starter credits, so this succeeds).
    gen = await client.post(
        f"/api/brands/{brand_id}/videos/generate",
        headers=auth_headers,
        json={"note": "fall menu launch"},
    )
    assert gen.status_code == 201
    job_id = gen.json()["id"]

    # The mock render completes on the first poll, storing a MediaAsset.
    polled = await client.post(f"/api/media-jobs/{job_id}/poll", headers=auth_headers)
    assert polled.status_code == 200
    assert polled.json()["status"] == "ready"

    assets = await client.get(
        f"/api/brands/{brand_id}/media-assets", headers=auth_headers
    )
    assert assets.status_code == 200
    asset = assets.json()[0]

    published = await client.post(
        f"/api/media-assets/{asset['id']}/publish",
        headers=auth_headers,
        json={"body": "test reel", "target_account_ids": account_ids},
    )
    assert published.status_code == 200
    item = published.json()
    assert item["content_type"] == "reel"
    assert asset["url"] in (item["media_urls"] or [])
    assert any(t["status"] == "published" for t in item["targets"])
