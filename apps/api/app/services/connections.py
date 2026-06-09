"""Persist OAuth-discovered accounts as SocialAccount rows (tokens encrypted)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_account import SocialAccount
from app.services.crypto import encrypt_secret
from app.services.meta.base import ConnectedAccount


async def upsert_connected_accounts(
    session: AsyncSession,
    brand_id: uuid.UUID,
    accounts: list[ConnectedAccount],
) -> list[SocialAccount]:
    """Create or update SocialAccount rows for a brand from a connect result."""
    saved: list[SocialAccount] = []
    for acct in accounts:
        existing = await session.scalar(
            select(SocialAccount).where(
                SocialAccount.brand_id == brand_id,
                SocialAccount.provider == acct.provider,
                SocialAccount.external_id == acct.external_id,
            )
        )
        row = existing or SocialAccount(
            brand_id=brand_id, provider=acct.provider, external_id=acct.external_id
        )
        row.display_name = acct.display_name
        row.ig_user_id = acct.ig_user_id
        row.access_token_encrypted = encrypt_secret(acct.access_token)
        row.scopes = acct.scopes
        row.status = "connected"
        if existing is None:
            session.add(row)
        saved.append(row)

    await session.commit()
    for row in saved:
        await session.refresh(row)
    return saved
