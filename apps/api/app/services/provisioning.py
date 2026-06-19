"""Idempotent provisioning of a personal Organization for a new Supabase user.

Supabase owns identity (`auth.users`); the first time we see an authenticated
user we create their personal Organization + owner Membership so app data has a
home.
"""

from __future__ import annotations

import uuid

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthenticatedUser
from app.models.membership import Membership, OrgRole
from app.models.organization import Organization


async def _find_personal_org(
    session: AsyncSession, user_uuid: uuid.UUID
) -> Organization | None:
    return await session.scalar(
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(
            Membership.user_id == user_uuid,
            Organization.is_personal.is_(True),
        )
    )


async def ensure_personal_org(session: AsyncSession, user: AuthenticatedUser) -> Organization:
    """Return the user's personal org, creating it on first call.

    Race-safe: a brand-new user's first page load fires several API calls in
    parallel, each of which may reach this function before any has committed.
    The personal-org slug is deterministic, so concurrent inserts collide on the
    unique constraint. We catch that, roll back, and return the org the winning
    request created — the caller never sees a 500, and exactly one org exists.
    """
    user_uuid = uuid.UUID(user.id)

    existing = await _find_personal_org(session, user_uuid)
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
    try:
        await session.flush()  # assigns org.id before the membership references it
        session.add(
            Membership(org_id=org.id, user_id=user_uuid, role=OrgRole.owner, email=user.email)
        )
        await session.commit()
    except IntegrityError:
        # A concurrent request won the create; reuse its org.
        await session.rollback()
        existing = await _find_personal_org(session, user_uuid)
        if existing is None:
            raise
        return existing

    await session.refresh(org)
    return org
