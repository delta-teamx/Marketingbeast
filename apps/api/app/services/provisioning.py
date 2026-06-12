"""Idempotent provisioning of a personal Organization for a new Supabase user.

Supabase owns identity (`auth.users`); the first time we see an authenticated
user we create their personal Organization + owner Membership so app data has a
home.
"""

from __future__ import annotations

import uuid

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthenticatedUser
from app.models.membership import Membership, OrgRole
from app.models.organization import Organization


async def ensure_personal_org(session: AsyncSession, user: AuthenticatedUser) -> Organization:
    """Return the user's personal org, creating it on first call."""
    user_uuid = uuid.UUID(user.id)

    existing = await session.scalar(
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(
            Membership.user_id == user_uuid,
            Organization.is_personal.is_(True),
        )
    )
    if existing:
        return existing

    label = user.email or f"user-{user.id[:8]}"
    base_slug = slugify(label) or "workspace"
    slug = f"{base_slug}-{user.id[:8]}"

    from app.core.config import get_settings

    org = Organization(
        name=label,
        slug=slug,
        is_personal=True,
        credit_balance=get_settings().starter_credits,
    )
    session.add(org)
    await session.flush()

    session.add(
        Membership(org_id=org.id, user_id=user_uuid, role=OrgRole.owner, email=user.email)
    )
    await session.commit()
    await session.refresh(org)
    return org
