"""The OAuth callback is a browser redirect target, so every outcome — success,
user-denied, expired state, bad code — must redirect back to the app, never
render a raw 4xx/5xx error page.
"""

from __future__ import annotations

from httpx import AsyncClient

from app.services.oauth_state import encode_state

CALLBACK = "/api/integrations/meta/oauth/callback"


async def _make_brand(client: AsyncClient, headers: dict[str, str]) -> str:
    await client.get("/api/auth/me", headers=headers)
    org = (await client.get("/api/organizations", headers=headers)).json()[0]
    brand = await client.post(
        "/api/brands", headers=headers, json={"org_id": org["id"], "name": "Acme"}
    )
    return brand.json()["id"]


async def test_callback_user_denied_redirects(client: AsyncClient) -> None:
    resp = await client.get(f"{CALLBACK}?error=access_denied&error_description=nope")
    assert resp.status_code in (302, 307)
    assert "connected=0" in resp.headers["location"]
    assert "reason=denied" in resp.headers["location"]


async def test_callback_missing_code_redirects(client: AsyncClient) -> None:
    resp = await client.get(f"{CALLBACK}?state=whatever")
    assert resp.status_code in (302, 307)
    assert "connected=0" in resp.headers["location"]


async def test_callback_invalid_state_redirects(client: AsyncClient) -> None:
    resp = await client.get(f"{CALLBACK}?code=abc123&state=not-a-real-jwt")
    assert resp.status_code in (302, 307)
    assert "reason=invalid_state" in resp.headers["location"]


async def test_callback_success_persists_and_redirects(
    client: AsyncClient, auth_headers: dict[str, str], user_id: str
) -> None:
    brand_id = await _make_brand(client, auth_headers)
    state = encode_state(brand_id=brand_id, user_id=user_id)

    resp = await client.get(f"{CALLBACK}?code=abc123&state={state}")
    assert resp.status_code in (302, 307)
    assert "connected=1" in resp.headers["location"]

    # Accounts were actually persisted for the brand.
    accounts = await client.get(
        f"/api/social-accounts?brand_id={brand_id}", headers=auth_headers
    )
    assert len(accounts.json()) >= 1
    assert all(a["status"] == "connected" for a in accounts.json())
