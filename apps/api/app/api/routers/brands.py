"""Brand CRUD (Phase 0: list + create), scoped to an organization."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_org_role
from app.core.security import AuthenticatedUser
from app.models.brand import Brand
from app.models.membership import OrgRole
from app.schemas.brand import BrandCreate, BrandOut

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("", response_model=list[BrandOut])
async def list_brands(
    org_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[Brand]:
    await require_org_role(org_id, session=session, user=user)
    rows = (
        await session.scalars(
            select(Brand).where(Brand.org_id == org_id).order_by(Brand.created_at)
        )
    ).all()
    return list(rows)


@router.post("", response_model=BrandOut, status_code=201)
async def create_brand(
    payload: BrandCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Brand:
    # Only owners/admins may add brands.
    await require_org_role(
        payload.org_id,
        session=session,
        user=user,
        allowed=(OrgRole.owner, OrgRole.admin),
    )
    brand = Brand(
        org_id=payload.org_id,
        name=payload.name,
        website_url=payload.website_url,
        industry_vertical=payload.industry_vertical,
    )
    session.add(brand)
    await session.commit()
    await session.refresh(brand)
    return brand
