"""AI video/reels: credits, generate, poll render, list jobs/assets."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.security import AuthenticatedUser
from app.models.content import ContentItem
from app.models.media import MediaAsset, MediaJob
from app.schemas.content import ContentItemOut
from app.schemas.media import (
    CreditsOut,
    MediaAssetOut,
    MediaJobOut,
    PublishReelIn,
    TopupIn,
    VideoGenerateIn,
)
from app.services.media import (
    InsufficientCredits,
    add_credits,
    generate_video,
    get_org_for_brand,
    poll_job,
    publish_media_asset,
)

router = APIRouter(prefix="/api", tags=["media"])


@router.get("/brands/{brand_id}/credits", response_model=CreditsOut)
async def get_credits(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CreditsOut:
    brand = await require_brand_access(brand_id, session=session, user=user)
    org = await get_org_for_brand(session, brand)
    return CreditsOut(org_id=org.id, credit_balance=org.credit_balance)


@router.post("/brands/{brand_id}/credits/topup", response_model=CreditsOut)
async def topup_credits(
    brand_id: uuid.UUID,
    payload: TopupIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CreditsOut:
    # Dev/mock top-up; real billing (Stripe) lands in Phase 8.
    brand = await require_brand_access(brand_id, session=session, user=user)
    org = await get_org_for_brand(session, brand)
    org = await add_credits(session, org, payload.amount)
    return CreditsOut(org_id=org.id, credit_balance=org.credit_balance)


@router.post("/brands/{brand_id}/videos/generate", response_model=MediaJobOut, status_code=201)
async def generate(
    brand_id: uuid.UUID,
    payload: VideoGenerateIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MediaJob:
    brand = await require_brand_access(brand_id, session=session, user=user)
    org = await get_org_for_brand(session, brand)
    try:
        return await generate_video(
            session,
            brand=brand,
            org=org,
            note=payload.note,
            product_url=payload.product_url,
            style=payload.style,
        )
    except InsufficientCredits as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc


@router.get("/brands/{brand_id}/media-jobs", response_model=list[MediaJobOut])
async def list_jobs(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[MediaJob]:
    await require_brand_access(brand_id, session=session, user=user)
    rows = (
        await session.scalars(
            select(MediaJob)
            .where(MediaJob.brand_id == brand_id)
            .order_by(MediaJob.created_at.desc())
        )
    ).all()
    return list(rows)


@router.post("/media-jobs/{job_id}/poll", response_model=MediaJobOut)
async def poll(
    job_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> MediaJob:
    job = await session.get(MediaJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    await require_brand_access(job.brand_id, session=session, user=user)
    return await poll_job(session, job)


@router.post("/media-assets/{asset_id}/publish", response_model=ContentItemOut)
async def publish_asset(
    asset_id: uuid.UUID,
    payload: PublishReelIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ContentItem:
    asset = await session.get(MediaAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Media asset not found")
    await require_brand_access(asset.brand_id, session=session, user=user)
    return await publish_media_asset(
        session,
        asset=asset,
        body=payload.body,
        target_account_ids=payload.target_account_ids,
        scheduled_time=payload.scheduled_time,
    )


@router.get("/brands/{brand_id}/media-assets", response_model=list[MediaAssetOut])
async def list_assets(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[MediaAsset]:
    await require_brand_access(brand_id, session=session, user=user)
    rows = (
        await session.scalars(
            select(MediaAsset)
            .where(MediaAsset.brand_id == brand_id)
            .order_by(MediaAsset.created_at.desc())
        )
    ).all()
    return list(rows)
