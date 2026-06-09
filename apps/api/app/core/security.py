"""Supabase Auth token validation.

The web app authenticates users via Supabase Auth (GoTrue). Supabase signs the
access token (JWT, HS256) with the project's JWT secret. The API trusts that
signature: we validate it here and extract the authenticated user.

We do NOT mint our own tokens or store passwords — identity lives in Supabase
`auth.users`.
"""

from __future__ import annotations

from dataclasses import dataclass

import jwt

from app.core.config import get_settings


@dataclass(frozen=True)
class AuthenticatedUser:
    """The Supabase user behind a request."""

    id: str  # auth.users.id (UUID as string) — the JWT `sub`
    email: str | None
    role: str | None


class TokenError(Exception):
    """Raised when a bearer token is missing or invalid."""


def decode_supabase_token(token: str) -> AuthenticatedUser:
    """Validate a Supabase access token and return the user.

    Raises TokenError on any failure (expired, bad signature, missing sub).
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            # Supabase tokens carry aud="authenticated" for signed-in users.
            audience="authenticated",
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:  # noqa: TRY003
        raise TokenError(str(exc)) from exc

    sub = payload.get("sub")
    if not sub:
        raise TokenError("token missing sub claim")

    return AuthenticatedUser(
        id=str(sub),
        email=payload.get("email"),
        role=payload.get("role"),
    )
