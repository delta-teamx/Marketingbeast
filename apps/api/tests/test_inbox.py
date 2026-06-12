"""DB-backed inbox smoke: sync → leads → draft reply → reply → hide."""

from __future__ import annotations

from httpx import AsyncClient


async def _brand_with_accounts(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)
    org = (await client.get("/api/organizations", headers=headers)).json()[0]
    brand_id = (
        await client.post(
            "/api/brands", headers=headers, json={"org_id": org["id"], "name": "Acme Coffee"}
        )
    ).json()["id"]
    await client.post(
        "/api/integrations/meta/connect-mock",
        headers=headers,
        json={"brand_id": brand_id, "code": "abcd"},
    )
    return brand_id


async def test_inbox_flow(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _brand_with_accounts(client, auth_headers)

    synced = await client.post(f"/api/brands/{brand_id}/inbox/sync", headers=auth_headers)
    assert synced.status_code == 200
    convs = synced.json()
    assert len(convs) >= 3
    # Buyer-intent conversations are flagged as leads and sort first.
    assert convs[0]["is_lead"] is True
    assert convs[0]["lead_score"] >= 40

    leads = await client.get(
        f"/api/brands/{brand_id}/inbox?leads_only=true", headers=auth_headers
    )
    assert all(c["is_lead"] for c in leads.json())
    assert len(leads.json()) >= 1

    lead = convs[0]
    detail = await client.get(f"/api/conversations/{lead['id']}", headers=auth_headers)
    assert len(detail.json()["messages"]) >= 1

    draft = await client.post(
        f"/api/conversations/{lead['id']}/draft-reply", headers=auth_headers
    )
    assert draft.json()["text"]

    replied = await client.post(
        f"/api/conversations/{lead['id']}/reply",
        headers=auth_headers,
        json={"text": draft.json()["text"]},
    )
    assert replied.json()["status"] == "replied"
    assert any(not m["is_inbound"] for m in replied.json()["messages"])

    # Moderate a casual comment.
    casual = next(c for c in convs if not c["is_lead"])
    hidden = await client.post(
        f"/api/conversations/{casual['id']}/hide", headers=auth_headers
    )
    assert hidden.json()["status"] == "hidden"


async def test_sync_is_idempotent(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _brand_with_accounts(client, auth_headers)
    first = await client.post(f"/api/brands/{brand_id}/inbox/sync", headers=auth_headers)
    second = await client.post(f"/api/brands/{brand_id}/inbox/sync", headers=auth_headers)
    # Re-syncing does not duplicate conversations.
    assert len(first.json()) == len(second.json())
