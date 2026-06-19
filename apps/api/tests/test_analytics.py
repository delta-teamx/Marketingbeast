"""DB-backed analytics smoke: sync insights → dashboard → report → competitors."""

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
    # Connect mock FB + IG so there are accounts to pull insights for.
    await client.post(
        "/api/integrations/meta/connect-mock",
        headers=headers,
        json={"brand_id": brand_id, "code": "xyz"},
    )
    return brand_id


async def test_sync_dashboard_report(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _brand_with_accounts(client, auth_headers)

    sync = await client.post(
        f"/api/brands/{brand_id}/insights/sync", headers=auth_headers
    )
    assert sync.status_code == 200
    dash = sync.json()
    assert dash["followers"] > 0
    assert len(dash["time_series"]) >= 7
    assert len(dash["per_account"]) == 2

    # Dashboard is retrievable without re-syncing.
    again = await client.get(f"/api/brands/{brand_id}/analytics", headers=auth_headers)
    assert again.json()["followers"] == dash["followers"]

    # Weekly report.
    report = await client.post(
        f"/api/brands/{brand_id}/reports/generate",
        headers=auth_headers,
        json={"period": "weekly"},
    )
    assert report.status_code == 200
    rep = report.json()
    assert rep["period"] == "weekly"
    assert rep["summary"]
    assert rep["metrics_json"]["reach"] > 0

    # Printable HTML report renders.
    html_resp = await client.get(f"/api/reports/{rep['id']}/html", headers=auth_headers)
    assert html_resp.status_code == 200
    assert "Acme Coffee" in html_resp.text


async def test_competitors_compare(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _brand_with_accounts(client, auth_headers)
    await client.post(f"/api/brands/{brand_id}/insights/sync", headers=auth_headers)

    await client.post(
        f"/api/brands/{brand_id}/competitors",
        headers=auth_headers,
        json={"name": "Rival Roasters", "followers": 999999, "engagement_rate": 4.2},
    )
    comp = await client.get(
        f"/api/brands/{brand_id}/competitors/compare", headers=auth_headers
    )
    assert comp.status_code == 200
    data = comp.json()
    assert data["competitors"][0]["name"] == "Rival Roasters"
    assert data["summary"]
