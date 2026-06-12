"""Analytics & reports: insights sync, dashboards, reports, competitors."""

from __future__ import annotations

import html
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.security import AuthenticatedUser
from app.models.analytics import Competitor, Report
from app.schemas.analytics import (
    CompetitorIn,
    CompetitorOut,
    DashboardOut,
    ReportGenerateIn,
    ReportOut,
)
from app.services.analytics import (
    add_competitor,
    build_report,
    compare_competitors,
    get_dashboard,
    ingest_brand_insights,
)

router = APIRouter(prefix="/api", tags=["analytics"])


@router.post("/brands/{brand_id}/insights/sync", response_model=DashboardOut)
async def sync_insights(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    brand = await require_brand_access(brand_id, session=session, user=user)
    await ingest_brand_insights(session, brand)
    return await get_dashboard(session, brand)


@router.get("/brands/{brand_id}/analytics", response_model=DashboardOut)
async def analytics(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Any:
    brand = await require_brand_access(brand_id, session=session, user=user)
    return await get_dashboard(session, brand)


@router.post("/brands/{brand_id}/reports/generate", response_model=ReportOut)
async def generate_report(
    brand_id: uuid.UUID,
    payload: ReportGenerateIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Report:
    brand = await require_brand_access(brand_id, session=session, user=user)
    return await build_report(session, brand, payload.period)


@router.get("/brands/{brand_id}/reports", response_model=list[ReportOut])
async def list_reports(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[Report]:
    await require_brand_access(brand_id, session=session, user=user)
    rows = (
        await session.scalars(
            select(Report).where(Report.brand_id == brand_id).order_by(Report.created_at.desc())
        )
    ).all()
    return list(rows)


@router.get("/reports/{report_id}/html", response_class=HTMLResponse)
async def report_html(
    report_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """A print-ready, white-label-able report page (browser → Save as PDF)."""
    report = await session.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    brand = await require_brand_access(report.brand_id, session=session, user=user)
    m = report.metrics_json
    rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{v:,}</td></tr>" for k, v in m.items()
    )
    name = html.escape(brand.name)
    period = report.period.value
    window = f"{report.starts_on} → {report.ends_on}"
    body = f"""<!doctype html><html><head><meta charset="utf-8">
<title>{name} — {period} report</title>
<style>body{{font:14px/1.5 system-ui;max-width:680px;margin:40px auto;color:#111}}
h1{{margin-bottom:0}}table{{width:100%;border-collapse:collapse;margin:16px 0}}
td{{border-bottom:1px solid #eee;padding:8px}}.muted{{color:#666}}</style></head>
<body>
<h1>{name}</h1>
<div class="muted">{period.title()} report · {window}</div>
<table>{rows}</table>
<p>{html.escape(report.summary)}</p>
</body></html>"""
    return HTMLResponse(content=body)


@router.post("/brands/{brand_id}/competitors", response_model=CompetitorOut, status_code=201)
async def create_competitor(
    brand_id: uuid.UUID,
    payload: CompetitorIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Competitor:
    await require_brand_access(brand_id, session=session, user=user)
    return await add_competitor(
        session,
        brand_id=brand_id,
        name=payload.name,
        handle=payload.handle,
        platform=payload.platform,
        followers=payload.followers,
        posting_frequency=payload.posting_frequency,
        engagement_rate=payload.engagement_rate,
    )


@router.get("/brands/{brand_id}/competitors", response_model=list[CompetitorOut])
async def list_competitors(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[Competitor]:
    await require_brand_access(brand_id, session=session, user=user)
    rows = (
        await session.scalars(select(Competitor).where(Competitor.brand_id == brand_id))
    ).all()
    return list(rows)


@router.get("/brands/{brand_id}/competitors/compare")
async def competitors_compare(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    brand = await require_brand_access(brand_id, session=session, user=user)
    return await compare_competitors(session, brand)
