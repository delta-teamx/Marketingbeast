"""List connected social accounts for a brand."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.security import AuthenticatedUser
from app.models.social_account import SocialAccount
from app.schemas.social_account import SocialAccountOut

router = APIRouter(prefix="/api/social-accounts", tags=["social-accounts"])


@router.get("", response_model=list[SocialAccountOut])
async def list_social_accounts(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[SocialAccount]:
    await require_brand_access(brand_id, session=session, user=user)
    rows = (
        await session.scalars(
            select(SocialAccount)
            .where(SocialAccount.brand_id == brand_id)
            .order_by(SocialAccount.created_at)
        )
    ).all()
    return list(rows)
