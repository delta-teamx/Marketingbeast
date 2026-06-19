"""Health endpoint smoke test — no DB required."""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient


async def test_health_ok() -> None:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
