"""Example Celery task. Proves the worker + broker wiring end to end."""

from __future__ import annotations

from app.worker.celery_app import celery_app


@celery_app.task(name="presence.ping")
def ping(value: str = "pong") -> str:
    """Trivial task used by the smoke test and as a template for real jobs."""
    return value
