"""Organization CRUD (Phase 0: list + create)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import AuthenticatedUser
from app.models.membership import Membership, OrgRole
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationOut

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationOut])
async def list_organizations(
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[Organization]:
    rows = (
        await session.scalars(
            select(Organization)
            .join(Membership, Membership.org_id == Organization.id)
            .where(Membership.user_id == uuid.UUID(user.id))
            .order_by(Organization.created_at)
        )
    ).all()
    return list(rows)


@router.post("", response_model=OrganizationOut, status_code=201)
async def create_organization(
    payload: OrganizationCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Organization:
    slug = f"{slugify(payload.name) or 'org'}-{uuid.uuid4().hex[:8]}"
    org = Organization(name=payload.name, slug=slug, is_personal=False)
    session.add(org)
    await session.flush()
    session.add(Membership(org_id=org.id, user_id=uuid.UUID(user.id), role=OrgRole.owner))
    await session.commit()
    await session.refresh(org)
    return org
