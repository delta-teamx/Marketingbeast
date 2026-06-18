"""Meta (Facebook/Instagram) connect flow.

- `oauth/start`   — authenticated; returns the Facebook login dialog URL.
- `oauth/callback`— public redirect target; trusts the signed `state`, exchanges
  the code, persists accounts, then bounces back to the web app.
- `connect-mock`  — dev/test only (META_MODE=mock): connect fake accounts without
  a browser round-trip.
"""

from __future__ import annotations

import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.config import get_settings
from app.core.security import AuthenticatedUser
from app.schemas.integration import ConnectMockIn, OAuthStartOut
from app.schemas.social_account import SocialAccountOut
from app.services.connections import upsert_connected_accounts
from app.services.meta import get_meta_client
from app.services.meta.base import MetaError
from app.services.oauth_state import decode_state, encode_state

router = APIRouter(prefix="/api/integrations/meta", tags=["integrations"])


def _connect_redirect(*, ok: bool, reason: str | None = None) -> RedirectResponse:
    """Bounce the user back to the dashboard with a connect status, never a raw
    error page — the callback is a browser redirect target, not a JSON API."""
    base = get_settings().web_app_url
    if ok:
        return RedirectResponse(url=f"{base}/dashboard?connected=1")
    suffix = f"&reason={reason}" if reason else ""
    return RedirectResponse(url=f"{base}/dashboard?connected=0{suffix}")


@router.get("/oauth/start", response_model=OAuthStartOut)
async def oauth_start(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OAuthStartOut:
    await require_brand_access(brand_id, session=session, user=user)
    state = encode_state(brand_id=str(brand_id), user_id=user.id)
    return OAuthStartOut(authorize_url=get_meta_client().build_oauth_url(state))


@router.get("/oauth/callback")
async def oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    # The user can deny the Facebook dialog — Meta then redirects here with an
    # `error` and no `code`. Always bounce back to the app, never a raw error.
    if error:
        return _connect_redirect(ok=False, reason="denied")
    if not code or not state:
        return _connect_redirect(ok=False, reason="missing_code")

    try:
        decoded = decode_state(state)
    except jwt.PyJWTError:
        # Expired (TTL) or tampered state — treat as a failed connect.
        return _connect_redirect(ok=False, reason="invalid_state")

    try:
        brand_id = uuid.UUID(decoded["brand_id"])
        accounts = await get_meta_client().exchange_code_for_accounts(code)
        await upsert_connected_accounts(session, brand_id, accounts)
    except MetaError:
        return _connect_redirect(ok=False, reason="exchange_failed")

    return _connect_redirect(ok=True)


@router.post("/connect-mock", response_model=list[SocialAccountOut])
async def connect_mock(
    payload: ConnectMockIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list:
    if get_settings().meta_mode != "mock":
        raise HTTPException(status_code=400, detail="connect-mock is disabled (META_MODE != mock)")
    await require_brand_access(payload.brand_id, session=session, user=user)
    accounts = await get_meta_client().exchange_code_for_accounts(payload.code)
    return await upsert_connected_accounts(session, payload.brand_id, accounts)
