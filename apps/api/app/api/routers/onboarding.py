"""Onboarding: capture a business + its marketing needs, create a Brand.

Creates the Brand under the user's personal org and stores an OnboardingProfile
so the AI can tune strategy. The web app then runs the audit on this brand.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import AuthenticatedUser
from app.models.brand import Brand
from app.models.onboarding import OnboardingProfile
from app.schemas.onboarding import (
    ConversationalIn,
    ConversationalOut,
    OnboardingIn,
    OnboardingOut,
)
from app.services.provisioning import ensure_personal_org
from app.services.verticals import vertical_profile

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.post("/conversational", response_model=ConversationalOut)
async def conversational_onboarding(
    payload: ConversationalIn,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ConversationalOut:
    """"Tell me about your business" → a tuned starter strategy (Phase 10)."""
    profile = vertical_profile(payload.message)
    pillars = profile["angles"][:4]
    summary = (
        f"Sounds like a {profile['label']} business. We'll use a "
        f"{profile['voice']} voice for {profile['audience']}, posting ~4–5x/week "
        f"around {', '.join(p.lower() for p in pillars)}."
    )
    return ConversationalOut(
        summary=summary,
        industry=profile["label"],
        suggested_goal="more_leads",
        suggested_cadence="4–5 posts per week",
        content_pillars=pillars,
    )


@router.post("", response_model=OnboardingOut, status_code=201)
async def submit_onboarding(
    payload: OnboardingIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OnboardingOut:
    org = await ensure_personal_org(session, user)

    brand = Brand(
        org_id=org.id,
        name=payload.business_name,
        website_url=payload.website_url,
        industry_vertical=payload.industry,
    )
    session.add(brand)
    await session.flush()

    profile = OnboardingProfile(
        brand_id=brand.id,
        goal=payload.goal,
        platforms=payload.platforms or None,
        posting_frequency=payload.posting_frequency,
        monthly_budget=payload.monthly_budget,
        biggest_challenge=payload.biggest_challenge,
        target_audience=payload.target_audience,
    )
    session.add(profile)
    await session.commit()
    await session.refresh(brand)
    await session.refresh(profile)
    return OnboardingOut.model_validate({"brand": brand, "profile": profile})


@router.get("", response_model=OnboardingOut | None)
async def latest_onboarding(
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> OnboardingOut | None:
    """Return the most recent onboarding profile for the user's brands, if any."""
    org = await ensure_personal_org(session, user)
    profile = await session.scalar(
        select(OnboardingProfile)
        .join(Brand, Brand.id == OnboardingProfile.brand_id)
        .where(Brand.org_id == org.id)
        .order_by(OnboardingProfile.created_at.desc())
        .limit(1)
    )
    if profile is None:
        return None
    brand = await session.get(Brand, profile.brand_id)
    return OnboardingOut.model_validate({"brand": brand, "profile": profile})
