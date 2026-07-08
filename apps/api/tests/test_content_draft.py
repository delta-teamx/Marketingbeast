"""A draft can be saved with no target accounts; scheduling still requires one."""

from __future__ import annotations

from httpx import AsyncClient


async def _brand(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)
    org = (await client.get("/api/organizations", headers=headers)).json()[0]
    resp = await client.post(
        "/api/brands", headers=headers, json={"org_id": org["id"], "name": "Acme"}
    )
    return resp.json()["id"]


async def test_save_draft_without_targets(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    brand_id = await _brand(client, auth_headers)
    resp = await client.post(
        "/api/content",
        headers=auth_headers,
        json={"brand_id": brand_id, "body": "a draft, no accounts connected yet"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "draft"
    assert data["targets"] == []


async def test_schedule_requires_a_target(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    brand_id = await _brand(client, auth_headers)
    resp = await client.post(
        "/api/content",
        headers=auth_headers,
        json={
            "brand_id": brand_id,
            "body": "scheduled but nowhere to publish",
            "target_account_ids": [],
            "scheduled_time": "2099-01-01T00:00:00+00:00",
        },
    )
    assert resp.status_code == 400
    assert "account" in resp.json()["detail"].lower()
