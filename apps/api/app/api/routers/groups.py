"""Niche detection + AI Facebook group suggestions (Tier A, advisory only)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.security import AuthenticatedUser
from app.models.group import GroupSuggestion
from app.schemas.group import (
    GenerateSuggestionsIn,
    GroupSuggestionOut,
    NicheProfileOut,
    SuggestionStatusUpdate,
)
from app.services.group_finder import detect_niche, suggest_groups
from app.services.website import fetch_site_text

router = APIRouter(prefix="/api", tags=["groups"])


async def _ensure_niche(session: AsyncSession, brand) -> NicheProfileOut:
    """Detect + persist the brand's niche if not already known."""
    if brand.niche_summary and brand.niche_keywords:
        return NicheProfileOut(
            category=brand.industry_vertical or "General",
            summary=brand.niche_summary,
            keywords=brand.niche_keywords,
        )
    text = await fetch_site_text(brand.website_url or "")
    niche = await detect_niche(
        brand_name=brand.name, website_text=text, vertical=brand.industry_vertical
    )
    brand.niche_summary = niche.summary
    brand.niche_keywords = niche.keywords
    if not brand.industry_vertical:
        brand.industry_vertical = niche.category
    await session.commit()
    return NicheProfileOut(**niche.model_dump())


@router.post("/brands/{brand_id}/niche/detect", response_model=NicheProfileOut)
async def detect_brand_niche(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> NicheProfileOut:
    brand = await require_brand_access(brand_id, session=session, user=user)
    # Force a fresh detection.
    brand.niche_summary = None
    brand.niche_keywords = None
    return await _ensure_niche(session, brand)


@router.post("/group-suggestions/generate", response_model=list[GroupSuggestionOut])
async def generate_suggestions(
    payload: GenerateSuggestionsIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[GroupSuggestion]:
    brand = await require_brand_access(payload.brand_id, session=session, user=user)
    niche_dict = await _ensure_niche(session, brand)
    from app.services.group_finder import NicheProfile

    suggestions = await suggest_groups(
        brand_name=brand.name, niche=NicheProfile(**niche_dict.model_dump())
    )
    rows = [
        GroupSuggestion(
            brand_id=brand.id,
            name=s.name,
            search_keyword=s.search_keyword,
            estimated_size=s.estimated_size,
            relevance_score=s.relevance_score,
            lead_quality_score=s.lead_quality_score,
            rationale=s.rationale,
            suggested_post_angle=s.suggested_post_angle,
        )
        for s in suggestions
    ]
    session.add_all(rows)
    await session.commit()
    for r in rows:
        await session.refresh(r)
    return rows


@router.get("/group-suggestions", response_model=list[GroupSuggestionOut])
async def list_suggestions(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[GroupSuggestion]:
    await require_brand_access(brand_id, session=session, user=user)
    rows = (
        await session.scalars(
            select(GroupSuggestion)
            .where(GroupSuggestion.brand_id == brand_id)
            .order_by(GroupSuggestion.relevance_score.desc())
        )
    ).all()
    return list(rows)


@router.patch("/group-suggestions/{suggestion_id}", response_model=GroupSuggestionOut)
async def update_suggestion(
    suggestion_id: uuid.UUID,
    payload: SuggestionStatusUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> GroupSuggestion:
    suggestion = await session.get(GroupSuggestion, suggestion_id)
    if suggestion is None:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    await require_brand_access(suggestion.brand_id, session=session, user=user)
    suggestion.status = payload.status
    await session.commit()
    await session.refresh(suggestion)
    return suggestion
