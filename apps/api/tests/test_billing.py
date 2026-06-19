"""DB-backed billing smoke (mock mode): checkout upgrades plan + grants credits."""

from __future__ import annotations

from httpx import AsyncClient


async def _org(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)
    return (await client.get("/api/organizations", headers=headers)).json()[0]["id"]


async def test_plans_catalog(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    resp = await client.get("/api/billing/plans", headers=auth_headers)
    assert resp.status_code == 200
    keys = {p["key"] for p in resp.json()}
    assert {"free", "growth", "agency"} <= keys


async def test_checkout_upgrades_and_grants_credits(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    org_id = await _org(client, auth_headers)

    out = await client.post(
        "/api/billing/checkout",
        headers=auth_headers,
        json={"org_id": org_id, "plan": "growth"},
    )
    assert out.status_code == 200
    body = out.json()
    assert body["completed"] is True  # mock applies instantly
    assert body["plan"] == "growth"
    assert body["credit_balance"] == 100 + 200  # starter + growth grant

    settings = await client.get(f"/api/organizations/{org_id}/settings", headers=auth_headers)
    assert settings.json()["plan"] == "growth"

    # Growth unlocks more brands (free allows 1; growth allows 3).
    for name in ("B1", "B2", "B3"):
        r = await client.post(
            "/api/brands", headers=auth_headers, json={"org_id": org_id, "name": name}
        )
        assert r.status_code == 201
