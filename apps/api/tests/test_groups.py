"""DB-backed smoke: niche → suggestions → track → queue a Tier B post."""

from __future__ import annotations

from httpx import AsyncClient


async def _make_brand(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)
    org = (await client.get("/api/organizations", headers=headers)).json()[0]
    brand = await client.post(
        "/api/brands",
        headers=headers,
        json={"org_id": org["id"], "name": "Acme Coffee", "website_url": "https://acme.test"},
    )
    return brand.json()["id"]


async def test_suggest_track_and_queue(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _make_brand(client, auth_headers)

    gen = await client.post(
        "/api/group-suggestions/generate", headers=auth_headers, json={"brand_id": brand_id}
    )
    assert gen.status_code == 200
    suggestions = gen.json()
    assert len(suggestions) >= 3
    assert all(0 <= s["relevance_score"] <= 100 for s in suggestions)

    # Listing returns them ranked.
    listed = await client.get(
        f"/api/group-suggestions?brand_id={brand_id}", headers=auth_headers
    )
    assert listed.status_code == 200
    top = suggestions[0]

    # Track the top suggestion.
    tracked = await client.patch(
        f"/api/group-suggestions/{top['id']}", headers=auth_headers, json={"status": "tracked"}
    )
    assert tracked.json()["status"] == "tracked"

    # Queue a Tier B post (backend stores it; nothing is posted).
    queued = await client.post(
        "/api/automation/group-queue",
        headers=auth_headers,
        json={
            "brand_id": brand_id,
            "group_suggestion_id": top["id"],
            "body": "Free tasting this weekend ☕",
        },
    )
    assert queued.status_code == 201
    assert queued.json()["status"] == "queued"  # never auto-posted

    q = await client.get(
        f"/api/automation/group-queue?brand_id={brand_id}", headers=auth_headers
    )
    assert len(q.json()) == 1


async def test_niche_detect_persists(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _make_brand(client, auth_headers)
    resp = await client.post(
        f"/api/brands/{brand_id}/niche/detect", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["category"]
    assert isinstance(body["keywords"], list)
