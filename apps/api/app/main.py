"""FastAPI application factory for the Presence API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    ads,
    agency,
    analytics,
    audit,
    auth,
    automation,
    billing,
    brands,
    content,
    groups,
    health,
    inbox,
    integrations_meta,
    media,
    onboarding,
    organizations,
    social_accounts,
)
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging

# The development default for SUPABASE_JWT_SECRET (also Supabase's own well-known
# local secret). Shipping this in production would let anyone mint valid HS256
# tokens, so we refuse to boot with it.
_DEV_JWT_SECRET = "super-secret-jwt-token-with-at-least-32-characters-long"


def _validate_production_settings(settings: Settings) -> None:
    """Fail fast at boot if production is missing critical secrets, rather than
    silently running with insecure defaults that only break (or get exploited)
    at request time."""
    if settings.api_env != "production":
        return
    problems: list[str] = []
    if settings.auth_mode == "supabase" and settings.supabase_jwt_secret == _DEV_JWT_SECRET:
        problems.append("SUPABASE_JWT_SECRET is still the insecure development default")
    if not settings.fernet_key:
        problems.append("FERNET_KEY is empty (required to encrypt stored OAuth tokens)")
    if problems:
        raise RuntimeError(
            "Refusing to start in production with insecure configuration: "
            + "; ".join(problems)
        )


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    _validate_production_settings(settings)

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
    app.include_router(onboarding.router)
    app.include_router(analytics.router)
    app.include_router(inbox.router)
    app.include_router(ads.router)
    app.include_router(media.router)
    app.include_router(agency.router)
    app.include_router(billing.router)
    return app


app = create_app()
