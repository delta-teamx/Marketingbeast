"""Auth-adjacent routes. Authentication itself is handled by Supabase Auth;
here we expose the current user and provision their personal org on first call.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import AuthenticatedUser
from app.models.membership import Membership
from app.schemas.user import MembershipOut, MeOut
from app.services.provisioning import ensure_personal_org

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=MeOut)
async def me(
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MeOut:
    # Idempotently ensure the user has a home org, then return memberships.
    await ensure_personal_org(session, user)
    memberships = (
        await session.scalars(
            select(Membership).where(Membership.user_id == uuid.UUID(user.id))
        )
    ).all()
    return MeOut(
        id=user.id,
        email=user.email,
        memberships=[MembershipOut.model_validate(m) for m in memberships],
    )
