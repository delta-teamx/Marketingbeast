"""Auth smoke tests: token validation and the 401 path (no DB required)."""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import TokenError, decode_supabase_token
from tests.conftest import make_token


async def test_me_requires_token() -> None:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/auth/me")

    assert resp.status_code == 401


def test_decode_valid_token_roundtrip() -> None:
    uid = str(uuid.uuid4())
    user = decode_supabase_token(make_token(uid, email="x@y.com"))
    assert user.id == uid
    assert user.email == "x@y.com"


def test_decode_rejects_garbage() -> None:
    with pytest.raises(TokenError):
        decode_supabase_token("not-a-jwt")
