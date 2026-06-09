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
from app.services.oauth_state import decode_state, encode_state

router = APIRouter(prefix="/api/integrations/meta", tags=["integrations"])


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
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    try:
        decoded = decode_state(state)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid state: {exc}") from exc

    brand_id = uuid.UUID(decoded["brand_id"])
    accounts = await get_meta_client().exchange_code_for_accounts(code)
    await upsert_connected_accounts(session, brand_id, accounts)
    return RedirectResponse(url=f"{settings.web_app_url}/dashboard?connected=1")


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
