"""DB-backed content engine smoke: generate → approve → repurpose."""

from __future__ import annotations

from httpx import AsyncClient


async def _make_brand(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)
    org = (await client.get("/api/organizations", headers=headers)).json()[0]
    brand = await client.post(
        "/api/brands", headers=headers, json={"org_id": org["id"], "name": "Acme Coffee"}
    )
    return brand.json()["id"]


async def test_generate_approve_repurpose(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    brand_id = await _make_brand(client, auth_headers)

    gen = await client.post(
        "/api/content/generate",
        headers=auth_headers,
        json={"brand_id": brand_id, "prompt": "fall menu launch", "count": 5},
    )
    assert gen.status_code == 201
    items = gen.json()
    assert len(items) == 5
    assert all(i["status"] == "draft" and i["approved"] is False for i in items)
    assert all(i["hashtags"] for i in items)

    # Approve the first draft.
    approved = await client.post(
        f"/api/content/{items[0]['id']}/approve", headers=auth_headers
    )
    assert approved.json()["approved"] is True

    # Repurpose it into post/reel/story.
    rep = await client.post(
        f"/api/content/{items[0]['id']}/repurpose", headers=auth_headers
    )
    assert rep.status_code == 201
    types = {i["content_type"] for i in rep.json()}
    assert types == {"post", "reel", "story"}

    # Best-times endpoint works.
    bt = await client.get(f"/api/content/best-times?brand_id={brand_id}", headers=auth_headers)
    assert bt.status_code == 200
    assert "Mon" in bt.json()
