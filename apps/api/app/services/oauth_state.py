"""Signed OAuth `state` tokens (CSRF protection for the Meta connect flow).

The state carries which brand + user initiated the connect, signed (HS256) and
short-lived so the callback can trust it.
"""

from __future__ import annotations

import time

import jwt

from app.core.config import get_settings

_PURPOSE = "meta-oauth-state"


def encode_state(*, brand_id: str, user_id: str, ttl_seconds: int = 600) -> str:
    settings = get_settings()
    payload = {
        "purpose": _PURPOSE,
        "brand_id": brand_id,
        "user_id": user_id,
        "exp": int(time.time()) + ttl_seconds,
    }
    return jwt.encode(payload, settings.supabase_jwt_secret, algorithm="HS256")


def decode_state(token: str) -> dict[str, str]:
    settings = get_settings()
    payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"])
    if payload.get("purpose") != _PURPOSE:
        raise jwt.InvalidTokenError("unexpected state purpose")
    return {"brand_id": payload["brand_id"], "user_id": payload["user_id"]}
