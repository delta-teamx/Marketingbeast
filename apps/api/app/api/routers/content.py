"""Content CRUD + publish. Scheduled items publish via the Celery beat poller;
'publish now' runs inline and returns the updated item.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.security import AuthenticatedUser
from app.models.content import ContentItem, ContentStatus
from app.models.social_account import SocialAccount
from app.schemas.content import ContentCreate, ContentItemOut
from app.services.publishing import create_content_item, publish_content_item

router = APIRouter(prefix="/api/content", tags=["content"])


@router.post("", response_model=ContentItemOut, status_code=201)
async def create_content(
    payload: ContentCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ContentItem:
    await require_brand_access(payload.brand_id, session=session, user=user)

    # Every target must be a connected account belonging to this brand.
    valid_ids = set(
        (
            await session.scalars(
                select(SocialAccount.id).where(SocialAccount.brand_id == payload.brand_id)
            )
        ).all()
    )
    if not set(payload.target_account_ids).issubset(valid_ids):
        raise HTTPException(status_code=400, detail="Target account does not belong to brand")

    return await create_content_item(
        session,
        brand_id=payload.brand_id,
        body=payload.body,
        content_type=payload.content_type,
        media_urls=payload.media_urls,
        target_account_ids=payload.target_account_ids,
        scheduled_time=payload.scheduled_time,
    )


@router.get("", response_model=list[ContentItemOut])
async def list_content(
    brand_id: uuid.UUID,
    status: ContentStatus | None = None,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[ContentItem]:
    await require_brand_access(brand_id, session=session, user=user)
    stmt = (
        select(ContentItem)
        .where(ContentItem.brand_id == brand_id)
        .options(selectinload(ContentItem.targets))
        .order_by(ContentItem.created_at.desc())
    )
    if status is not None:
        stmt = stmt.where(ContentItem.status == status)
    return list((await session.scalars(stmt)).all())


@router.post("/{item_id}/publish", response_model=ContentItemOut)
async def publish_now(
    item_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ContentItem:
    item = await session.get(ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Content item not found")
    await require_brand_access(item.brand_id, session=session, user=user)
    return await publish_content_item(session, item_id)
