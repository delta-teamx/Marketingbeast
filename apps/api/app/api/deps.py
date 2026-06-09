"""Shared FastAPI dependencies: DB session, current user, org-role guard."""

from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthenticatedUser, TokenError, decode_supabase_token
from app.db.session import get_session
from app.models.membership import Membership, OrgRole

# Re-export the DB dependency under an API-friendly name.
get_db = get_session


async def get_current_user(
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser:
    """Validate the Supabase bearer token and return the user."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        return decode_supabase_token(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def require_org_role(
    org_id: uuid.UUID,
    *,
    session: AsyncSession,
    user: AuthenticatedUser,
    allowed: tuple[OrgRole, ...] = (OrgRole.owner, OrgRole.admin, OrgRole.member),
) -> Membership:
    """Ensure the user belongs to `org_id` with one of the allowed roles."""
    membership = await session.scalar(
        select(Membership).where(
            Membership.org_id == org_id,
            Membership.user_id == uuid.UUID(user.id),
        )
    )
    if membership is None or membership.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this organization",
        )
    return membership


CurrentUser = Depends(get_current_user)
DbSession = Depends(get_db)
