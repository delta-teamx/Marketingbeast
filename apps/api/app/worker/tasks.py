"""Celery tasks. Scheduled content is published by the `publish_due` beat job.

Each task creates its own async engine/session so loops never cross between
Celery's sync workers (asyncpg connections are loop-bound).
"""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.publishing import publish_due_content
from app.worker.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="presence.ping")
def ping(value: str = "pong") -> str:
    """Trivial task used by the smoke test and as a template for real jobs."""
    return value


async def _publish_due_async() -> list[str]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            ids = await publish_due_content(session)
            return [str(i) for i in ids]
    finally:
        await engine.dispose()


@celery_app.task(name="presence.publish_due")
def publish_due() -> list[str]:
    """Publish every scheduled item whose time has arrived (runs on a beat)."""
    published = asyncio.run(_publish_due_async())
    if published:
        logger.info("published %d due item(s): %s", len(published), published)
    return published


async def _ingest_all_insights_async() -> int:
    from sqlalchemy import select

    from app.models.brand import Brand
    from app.services.analytics import ingest_brand_insights

    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            brands = (await session.scalars(select(Brand))).all()
            total = 0
            for brand in brands:
                total += await ingest_brand_insights(session, brand, days=1)
            return total
    finally:
        await engine.dispose()


@celery_app.task(name="presence.ingest_insights")
def ingest_insights() -> int:
    """Daily insights ingestion for every brand (runs on a beat)."""
    written = asyncio.run(_ingest_all_insights_async())
    logger.info("ingested %d insight snapshot(s)", written)
    return written


async def _poll_renders_async() -> int:
    from app.services.media import poll_rendering_jobs

    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            return await poll_rendering_jobs(session)
    finally:
        await engine.dispose()


@celery_app.task(name="presence.poll_renders")
def poll_renders() -> int:
    """Advance in-flight media render jobs (runs on a beat)."""
    advanced = asyncio.run(_poll_renders_async())
    if advanced:
        logger.info("polled %d render job(s)", advanced)
    return advanced
