"""FastAPI application factory for the Presence API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    audit,
    auth,
    automation,
    brands,
    content,
    groups,
    health,
    integrations_meta,
    organizations,
    social_accounts,
)
from app.core.config import get_settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title="Presence API",
        version="0.0.0",
        description="Tier A — official-API-first social marketing backend",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(organizations.router)
    app.include_router(brands.router)
    app.include_router(social_accounts.router)
    app.include_router(integrations_meta.router)
    app.include_router(content.router)
    app.include_router(groups.router)
    app.include_router(automation.router)
    app.include_router(audit.router)
    return app


app = create_app()
