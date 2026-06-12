"""Agency layer: team members, invites, plan, and white-label settings."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_org_role
from app.core.security import AuthenticatedUser
from app.models.invite import OrgInvite
from app.models.membership import Membership, OrgRole
from app.models.organization import Organization
from app.schemas.agency import (
    InviteCreate,
    InviteOut,
    MemberOut,
    OrgSettingsOut,
    PlanUpdate,
    RoleUpdate,
    WhiteLabelIn,
)
from app.services import agency
from app.services.billing import set_plan

router = APIRouter(prefix="/api", tags=["agency"])

_ADMIN = (OrgRole.owner, OrgRole.admin)


async def _org(session: AsyncSession, org_id: uuid.UUID) -> Organization:
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


# --- Settings ---


@router.get("/organizations/{org_id}/settings", response_model=OrgSettingsOut)
async def org_settings(
    org_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Organization:
    await require_org_role(org_id, session=session, user=user)
    return await _org(session, org_id)


@router.put("/organizations/{org_id}/white-label", response_model=OrgSettingsOut)
async def update_white_label(
    org_id: uuid.UUID,
    payload: WhiteLabelIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Organization:
    await require_org_role(org_id, session=session, user=user, allowed=_ADMIN)
    org = await _org(session, org_id)
    return await agency.update_white_label(session, org, payload.model_dump(exclude_none=True))


@router.post("/organizations/{org_id}/plan", response_model=OrgSettingsOut)
async def change_plan(
    org_id: uuid.UUID,
    payload: PlanUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Organization:
    await require_org_role(org_id, session=session, user=user, allowed=(OrgRole.owner,))
    org = await _org(session, org_id)
    return await set_plan(session, org, payload.plan)


# --- Members ---


@router.get("/organizations/{org_id}/members", response_model=list[MemberOut])
async def list_members(
    org_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[Membership]:
    await require_org_role(org_id, session=session, user=user)
    return await agency.list_members(session, org_id)


async def _member(session: AsyncSession, org_id: uuid.UUID, membership_id: uuid.UUID) -> Membership:
    m = await session.get(Membership, membership_id)
    if m is None or m.org_id != org_id:
        raise HTTPException(status_code=404, detail="Member not found")
    return m


@router.patch("/organizations/{org_id}/members/{membership_id}", response_model=MemberOut)
async def update_member(
    org_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: RoleUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Membership:
    await require_org_role(org_id, session=session, user=user, allowed=(OrgRole.owner,))
    member = await _member(session, org_id, membership_id)
    return await agency.update_member_role(session, member, payload.role)


@router.delete("/organizations/{org_id}/members/{membership_id}", status_code=204)
async def remove_member(
    org_id: uuid.UUID,
    membership_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> None:
    await require_org_role(org_id, session=session, user=user, allowed=(OrgRole.owner,))
    await agency.remove_member(session, await _member(session, org_id, membership_id))


# --- Invites ---


@router.post("/organizations/{org_id}/invites", response_model=InviteOut, status_code=201)
async def create_invite(
    org_id: uuid.UUID,
    payload: InviteCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OrgInvite:
    await require_org_role(org_id, session=session, user=user, allowed=_ADMIN)
    org = await _org(session, org_id)
    return await agency.create_invite(session, org, payload.email, payload.role)


@router.get("/organizations/{org_id}/invites", response_model=list[InviteOut])
async def list_invites(
    org_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[OrgInvite]:
    await require_org_role(org_id, session=session, user=user, allowed=_ADMIN)
    return await agency.list_invites(session, org_id)


@router.get("/invites", response_model=list[InviteOut])
async def my_invites(
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[OrgInvite]:
    return await agency.my_pending_invites(session, user.email or "")


@router.post("/invites/{invite_id}/accept", response_model=MemberOut)
async def accept_invite(
    invite_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Membership:
    invite = await session.get(OrgInvite, invite_id)
    if invite is None:
        raise HTTPException(status_code=404, detail="Invite not found")
    return await agency.accept_invite(session, invite, user)
