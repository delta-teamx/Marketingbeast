"""Supabase Auth token validation.

The web app authenticates users via Supabase Auth (GoTrue). Supabase signs the
access token (JWT) and the API trusts that signature: we validate it here and
extract the authenticated user.

Supabase projects can sign tokens one of two ways:

* **Asymmetric signing keys** (the current default for new projects) — tokens
  use ES256/RS256 and are verified against the project's public JWKS, served at
  ``{SUPABASE_URL}/auth/v1/.well-known/jwks.json``.
* **Legacy HS256 shared secret** — tokens are verified with
  ``SUPABASE_JWT_SECRET``.

We support both, branching on the token's ``alg`` header. HS256 tokens are only
ever verified with the shared secret (never a JWKS public key), which avoids the
classic RS/HS algorithm-confusion attack.

We do NOT mint our own tokens or store passwords — identity lives in Supabase
`auth.users`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from app.core.config import get_settings

# Asymmetric algorithms we accept for JWKS-verified tokens.
_ASYMMETRIC_ALGS = ("ES256", "RS256")


@dataclass(frozen=True)
class AuthenticatedUser:
    """The Supabase user behind a request."""

    id: str  # auth.users.id (UUID as string) — the JWT `sub`
    email: str | None
    role: str | None


class TokenError(Exception):
    """Raised when a bearer token is missing or invalid."""


@lru_cache
def _jwks_client() -> PyJWKClient:
    """Cached JWKS client for the project's public signing keys.

    PyJWKClient caches fetched keys internally, so we only hit Supabase when an
    unseen `kid` appears (e.g. after a key rotation).
    """
    base = get_settings().supabase_url.rstrip("/")
    return PyJWKClient(f"{base}/auth/v1/.well-known/jwks.json")


def decode_supabase_token(token: str) -> AuthenticatedUser:
    """Validate a Supabase access token and return the user.

    Raises TokenError on any failure (expired, bad signature, missing sub).
    """
    settings = get_settings()
    # Supabase tokens carry aud="authenticated" for signed-in users.
    common = {"audience": "authenticated", "options": {"require": ["exp", "sub"]}}
    try:
        alg = jwt.get_unverified_header(token).get("alg", "")
        if alg == "HS256":
            payload = jwt.decode(
                token, settings.supabase_jwt_secret, algorithms=["HS256"], **common
            )
        elif alg in _ASYMMETRIC_ALGS:
            signing_key = _jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(token, signing_key.key, algorithms=[alg], **common)
        else:
            raise TokenError(f"unsupported token algorithm: {alg or 'none'}")
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
