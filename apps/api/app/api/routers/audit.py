"""Flagship URL→Presence audit: run, fetch latest, and seed the first week."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.security import AuthenticatedUser
from app.models.audit import AuditReport
from app.schemas.audit import AuditReportOut
from app.schemas.content import ContentItemOut
from app.services.audit import run_audit, seed_drafts_from_plan

router = APIRouter(prefix="/api/brands/{brand_id}/audit", tags=["audit"])


@router.post("/run", response_model=AuditReportOut)
async def run_brand_audit(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AuditReport:
    brand = await require_brand_access(brand_id, session=session, user=user)
    result = await run_audit(session, brand)
    report = AuditReport(
        brand_id=brand.id,
        overall_score=result.overall_score,
        overall_grade=result.overall_grade,
        sections=result.sections,
        findings=result.findings,
        recommendations=result.recommendations,
        strategy_brief=result.strategy_brief,
        content_plan=result.content_plan,
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


@router.get("", response_model=AuditReportOut | None)
async def latest_audit(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> AuditReport | None:
    await require_brand_access(brand_id, session=session, user=user)
    return await session.scalar(
        select(AuditReport)
        .where(AuditReport.brand_id == brand_id)
        .order_by(AuditReport.created_at.desc())
        .limit(1)
    )


@router.post("/seed", response_model=list[ContentItemOut])
async def seed_first_week(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list:
    """Turn the latest audit's content plan into draft posts ("start running my account")."""
    await require_brand_access(brand_id, session=session, user=user)
    report = await session.scalar(
        select(AuditReport)
        .where(AuditReport.brand_id == brand_id)
        .order_by(AuditReport.created_at.desc())
        .limit(1)
    )
    if report is None or not report.content_plan:
        raise HTTPException(status_code=400, detail="Run an audit first")
    return await seed_drafts_from_plan(session, brand_id=brand_id, plan=report.content_plan)
