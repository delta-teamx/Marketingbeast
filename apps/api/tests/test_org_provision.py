"""DB-backed smoke test: first /me provisions a personal org, then it's listable."""

from __future__ import annotations

from httpx import AsyncClient


async def test_me_provisions_personal_org(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    # First authenticated call provisions a personal org.
    me = await client.get("/api/auth/me", headers=auth_headers)
    assert me.status_code == 200
    body = me.json()
    assert len(body["memberships"]) == 1
    assert body["memberships"][0]["role"] == "owner"

    # The org is now listable for this user.
    orgs = await client.get("/api/organizations", headers=auth_headers)
    assert orgs.status_code == 200
    data = orgs.json()
    assert len(data) == 1
    assert data[0]["is_personal"] is True

    # Idempotent: calling /me again does not create a second org.
    await client.get("/api/auth/me", headers=auth_headers)
    orgs2 = await client.get("/api/organizations", headers=auth_headers)
    assert len(orgs2.json()) == 1


async def test_create_org_and_brand(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await client.get("/api/auth/me", headers=auth_headers)  # provision

    created = await client.post(
        "/api/organizations", headers=auth_headers, json={"name": "Acme Agency"}
    )
    assert created.status_code == 201
    org_id = created.json()["id"]

    brand = await client.post(
        "/api/brands",
        headers=auth_headers,
        json={"org_id": org_id, "name": "Acme Coffee", "website_url": "https://acme.test"},
    )
    assert brand.status_code == 201
    assert brand.json()["name"] == "Acme Coffee"

    listing = await client.get(f"/api/brands?org_id={org_id}", headers=auth_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
