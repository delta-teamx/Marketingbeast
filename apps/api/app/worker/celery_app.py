"""Celery application. Redis is the broker and result backend.

Background jobs (scheduled publishing, audits, report generation) attach here in
later phases. Phase 0 ships the wiring + one example task.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "presence",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Beat: poll for scheduled content that's due and publish it.
    beat_schedule={
        "publish-due-content": {
            "task": "presence.publish_due",
            "schedule": settings.publish_poll_seconds,
        },
        "ingest-insights-daily": {
            "task": "presence.ingest_insights",
            "schedule": 24 * 60 * 60.0,  # once a day
        },
    },
)
