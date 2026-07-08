"""Ads Manager: connect ad accounts, launch campaigns, sync, recommend."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.config import get_settings
from app.core.security import AuthenticatedUser
from app.models.ads import AdAccount, AdCampaign, CampaignStatus
from app.schemas.ads import (
    AdAccountOut,
    CampaignCreate,
    CampaignDetailOut,
    CampaignOut,
    StatusUpdate,
)
from app.services.ads import (
    connect_mock_account,
    launch_campaign,
    load_campaign,
    recommendations,
    set_campaign_status,
    sync_campaign_insights,
)

router = APIRouter(prefix="/api", tags=["ads"])


@router.post("/brands/{brand_id}/ad-accounts/connect-mock", response_model=AdAccountOut)
async def connect_ad_account(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdAccount:
    if get_settings().meta_mode != "mock":
        raise HTTPException(
            status_code=400,
            detail=(
                "Ads Manager isn't available yet in live mode — it needs Meta "
                "Marketing API access (ads_management) and App Review. It's fully "
                "usable in demo mode."
            ),
        )
    brand = await require_brand_access(brand_id, session=session, user=user)
    return await connect_mock_account(session, brand)


@router.get("/brands/{brand_id}/ad-accounts", response_model=list[AdAccountOut])
async def list_ad_accounts(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[AdAccount]:
    await require_brand_access(brand_id, session=session, user=user)
    rows = (
        await session.scalars(select(AdAccount).where(AdAccount.brand_id == brand_id))
    ).all()
    return list(rows)


@router.post("/brands/{brand_id}/campaigns", response_model=CampaignDetailOut, status_code=201)
async def create_campaign(
    brand_id: uuid.UUID,
    payload: CampaignCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdCampaign:
    brand = await require_brand_access(brand_id, session=session, user=user)
    account = await session.get(AdAccount, payload.ad_account_id)
    if account is None or account.brand_id != brand_id:
        raise HTTPException(status_code=400, detail="Ad account does not belong to brand")
    return await launch_campaign(
        session,
        brand=brand,
        ad_account=account,
        name=payload.name,
        objective=payload.objective,
        daily_budget=payload.daily_budget,
        concept=payload.concept,
        n_variations=payload.n_variations,
    )


@router.get("/brands/{brand_id}/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[AdCampaign]:
    await require_brand_access(brand_id, session=session, user=user)
    rows = (
        await session.scalars(
            select(AdCampaign)
            .where(AdCampaign.brand_id == brand_id)
            .order_by(AdCampaign.created_at.desc())
        )
    ).all()
    return list(rows)


async def _campaign_for_user(
    session: AsyncSession, campaign_id: uuid.UUID, user: AuthenticatedUser
) -> AdCampaign:
    campaign = await load_campaign(session, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    await require_brand_access(campaign.brand_id, session=session, user=user)
    return campaign


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetailOut)
async def campaign_detail(
    campaign_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdCampaign:
    return await _campaign_for_user(session, campaign_id, user)


@router.post("/campaigns/{campaign_id}/sync", response_model=CampaignDetailOut)
async def sync_campaign(
    campaign_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdCampaign:
    campaign = await _campaign_for_user(session, campaign_id, user)
    return await sync_campaign_insights(session, campaign)


@router.get("/campaigns/{campaign_id}/recommendations")
async def campaign_recommendations(
    campaign_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    campaign = await _campaign_for_user(session, campaign_id, user)
    return recommendations(campaign)


@router.patch("/campaigns/{campaign_id}/status", response_model=CampaignDetailOut)
async def update_campaign_status(
    campaign_id: uuid.UUID,
    payload: StatusUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AdCampaign:
    campaign = await _campaign_for_user(session, campaign_id, user)
    if payload.status == CampaignStatus.draft:
        raise HTTPException(status_code=400, detail="Cannot set a campaign back to draft")
    return await set_campaign_status(session, campaign, payload.status)
