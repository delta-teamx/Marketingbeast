"""Agency team management: invites, members, white-label."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AuthenticatedUser
from app.models.invite import InviteStatus, OrgInvite
from app.models.membership import Membership, OrgRole
from app.models.organization import Organization
from app.services.billing import ensure_can_add_seat

WHITE_LABEL_FIELDS = {"brand_name", "logo_url", "primary_color", "custom_domain"}


async def create_invite(
    session: AsyncSession, org: Organization, email: str, role: OrgRole
) -> OrgInvite:
    existing = await session.scalar(
        select(OrgInvite).where(
            OrgInvite.org_id == org.id,
            OrgInvite.email == email.lower(),
            OrgInvite.status == InviteStatus.pending,
        )
    )
    if existing:
        return existing
    invite = OrgInvite(
        org_id=org.id, email=email.lower(), role=role, token=uuid.uuid4().hex
    )
    session.add(invite)
    await session.commit()
    await session.refresh(invite)
    return invite


async def list_invites(session: AsyncSession, org_id: uuid.UUID) -> list[OrgInvite]:
    return list(
        (
            await session.scalars(
                select(OrgInvite)
                .where(OrgInvite.org_id == org_id)
                .order_by(OrgInvite.created_at.desc())
            )
        ).all()
    )


async def my_pending_invites(session: AsyncSession, email: str) -> list[OrgInvite]:
    return list(
        (
            await session.scalars(
                select(OrgInvite).where(
                    OrgInvite.email == email.lower(),
                    OrgInvite.status == InviteStatus.pending,
                )
            )
        ).all()
    )


async def accept_invite(
    session: AsyncSession, invite: OrgInvite, user: AuthenticatedUser
) -> Membership:
    if user.email and invite.email.lower() != user.email.lower():
        raise HTTPException(status_code=403, detail="This invite is for a different email")
    if invite.status != InviteStatus.pending:
        raise HTTPException(status_code=409, detail="Invite is no longer pending")

    user_uuid = uuid.UUID(user.id)
    existing = await session.scalar(
        select(Membership).where(
            Membership.org_id == invite.org_id, Membership.user_id == user_uuid
        )
    )
    if existing is None:
        org = await session.get(Organization, invite.org_id)
        await ensure_can_add_seat(session, org)
        existing = Membership(
            org_id=invite.org_id, user_id=user_uuid, role=invite.role, email=user.email
        )
        session.add(existing)

    invite.status = InviteStatus.accepted
    await session.commit()
    await session.refresh(existing)
    return existing


async def list_members(session: AsyncSession, org_id: uuid.UUID) -> list[Membership]:
    return list(
        (
            await session.scalars(
                select(Membership)
                .where(Membership.org_id == org_id)
                .order_by(Membership.created_at)
            )
        ).all()
    )


async def _owner_count(session: AsyncSession, org_id: uuid.UUID) -> int:
    return (
        await session.scalar(
            select(func.count(Membership.id)).where(
                Membership.org_id == org_id, Membership.role == OrgRole.owner
            )
        )
    ) or 0


async def update_member_role(
    session: AsyncSession, membership: Membership, role: OrgRole
) -> Membership:
    if (
        membership.role == OrgRole.owner
        and role != OrgRole.owner
        and await _owner_count(session, membership.org_id) <= 1
    ):
        raise HTTPException(status_code=400, detail="Cannot demote the last owner")
    membership.role = role
    await session.commit()
    await session.refresh(membership)
    return membership


async def remove_member(session: AsyncSession, membership: Membership) -> None:
    if membership.role == OrgRole.owner and await _owner_count(session, membership.org_id) <= 1:
        raise HTTPException(status_code=400, detail="Cannot remove the last owner")
    await session.delete(membership)
    await session.commit()


async def update_white_label(
    session: AsyncSession, org: Organization, data: dict[str, Any]
) -> Organization:
    current = dict(org.white_label_json or {})
    for key in WHITE_LABEL_FIELDS:
        if key in data:
            current[key] = data[key]
    org.white_label_json = current
    await session.commit()
    await session.refresh(org)
    return org
