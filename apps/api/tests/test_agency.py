"""DB-backed agency smoke: plan limits, white-label, invite → accept."""

from __future__ import annotations

import uuid

from httpx import AsyncClient

from tests.conftest import make_token


async def _personal_org(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)
    return (await client.get("/api/organizations", headers=headers)).json()[0]["id"]


async def test_plan_limits_and_upgrade(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    org_id = await _personal_org(client, auth_headers)

    # Free plan: 1 brand allowed.
    b1 = await client.post(
        "/api/brands", headers=auth_headers, json={"org_id": org_id, "name": "Brand 1"}
    )
    assert b1.status_code == 201
    b2 = await client.post(
        "/api/brands", headers=auth_headers, json={"org_id": org_id, "name": "Brand 2"}
    )
    assert b2.status_code == 402  # plan limit

    # Upgrade unlocks more brands.
    up = await client.post(
        f"/api/organizations/{org_id}/plan", headers=auth_headers, json={"plan": "agency"}
    )
    assert up.json()["plan"] == "agency"
    b2b = await client.post(
        "/api/brands", headers=auth_headers, json={"org_id": org_id, "name": "Brand 2"}
    )
    assert b2b.status_code == 201


async def test_white_label(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    org_id = await _personal_org(client, auth_headers)
    resp = await client.put(
        f"/api/organizations/{org_id}/white-label",
        headers=auth_headers,
        json={"brand_name": "Acme Agency", "primary_color": "#ff0066"},
    )
    assert resp.status_code == 200
    assert resp.json()["white_label_json"]["brand_name"] == "Acme Agency"

    settings = await client.get(
        f"/api/organizations/{org_id}/settings", headers=auth_headers
    )
    assert settings.json()["white_label_json"]["primary_color"] == "#ff0066"


async def test_invite_and_accept(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    org_id = await _personal_org(client, auth_headers)
    # Agency plan so there's room for a second seat.
    await client.post(
        f"/api/organizations/{org_id}/plan", headers=auth_headers, json={"plan": "agency"}
    )

    invited = await client.post(
        f"/api/organizations/{org_id}/invites",
        headers=auth_headers,
        json={"email": "teammate@example.com", "role": "admin"},
    )
    assert invited.status_code == 201

    # A second user with the invited email.
    b_id = str(uuid.uuid4())
    b_headers = {"Authorization": f"Bearer {make_token(b_id, email='teammate@example.com')}"}
    await client.get("/api/auth/me", headers=b_headers)  # provision B's own org

    pending = await client.get("/api/invites", headers=b_headers)
    assert len(pending.json()) == 1
    invite_id = pending.json()[0]["id"]

    accepted = await client.post(f"/api/invites/{invite_id}/accept", headers=b_headers)
    assert accepted.status_code == 200
    assert accepted.json()["role"] == "admin"

    members = await client.get(f"/api/organizations/{org_id}/members", headers=auth_headers)
    emails = {m["email"] for m in members.json()}
    assert "teammate@example.com" in emails

    # Cannot demote the last owner.
    owner = next(m for m in members.json() if m["role"] == "owner")
    bad = await client.patch(
        f"/api/organizations/{org_id}/members/{owner['id']}",
        headers=auth_headers,
        json={"role": "member"},
    )
    assert bad.status_code == 400
