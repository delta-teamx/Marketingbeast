"""DB-backed flagship audit smoke: run → report → seed first week."""

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


async def test_run_audit_and_seed(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _make_brand(client, auth_headers)

    run = await client.post(f"/api/brands/{brand_id}/audit/run", headers=auth_headers)
    assert run.status_code == 200
    report = run.json()
    assert report["overall_grade"] in {"A", "B", "C", "D", "F"}
    assert 0 <= report["overall_score"] <= 100
    assert len(report["sections"]) == 5
    assert len(report["content_plan"]) == 7
    assert report["strategy_brief"]

    # Latest audit is retrievable.
    latest = await client.get(f"/api/brands/{brand_id}/audit", headers=auth_headers)
    assert latest.json()["id"] == report["id"]

    # Seeding turns the plan into draft posts.
    seeded = await client.post(f"/api/brands/{brand_id}/audit/seed", headers=auth_headers)
    assert seeded.status_code == 200
    assert len(seeded.json()) == 7
    assert all(item["status"] == "draft" for item in seeded.json())

    # Those drafts now show up in the content list.
    content = await client.get(f"/api/content?brand_id={brand_id}", headers=auth_headers)
    assert len(content.json()) == 7


async def test_seed_requires_audit(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    brand_id = await _make_brand(client, auth_headers)
    resp = await client.post(f"/api/brands/{brand_id}/audit/seed", headers=auth_headers)
    assert resp.status_code == 400
