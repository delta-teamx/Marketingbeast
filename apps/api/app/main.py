"""FastAPI application factory for the Presence API."""

from __future__ import annotations

import logging

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
    """Keep production secure without taking the whole server down over a single
    stray env var. Where we can run securely, self-correct and warn loudly; only
    refuse to boot when there is genuinely no safe way to run."""
    if settings.api_env != "production":
        return
    logger = logging.getLogger("presence.startup")

    # AUTH_MODE=dev hands every request a fixed demo user with no token check — a
    # full auth bypass. But rather than crash the entire deployment, disable the
    # bypass and fall back to real Supabase auth whenever we have a usable JWT
    # secret. The server stays UP and secure; only a config with no secure path
    # (below) refuses to boot.
    if settings.auth_mode == "dev" and (
        settings.supabase_jwt_secret and settings.supabase_jwt_secret != _DEV_JWT_SECRET
    ):
        logger.critical(
            "AUTH_MODE=dev is not permitted in production — overriding to supabase auth. "
            "Set AUTH_MODE=supabase in the environment to remove this override."
        )
        settings.auth_mode = "supabase"

    problems: list[str] = []
    if settings.auth_mode == "dev":
        problems.append(
            "AUTH_MODE=dev is a development-only auth bypass and no valid "
            "SUPABASE_JWT_SECRET is set to fall back to (set AUTH_MODE=supabase + secret)"
        )
    if settings.auth_mode == "supabase" and settings.supabase_jwt_secret == _DEV_JWT_SECRET:
        problems.append("SUPABASE_JWT_SECRET is still the insecure development default")
    if not settings.fernet_key:
        problems.append("FERNET_KEY is empty (required to encrypt stored OAuth tokens)")
    if problems:
        raise RuntimeError(
            "Refusing to start in production with insecure configuration: "
            + "; ".join(problems)
        )

    # Providers still on the in-process mock won't break the app, but they aren't
    # real — surface them loudly so a production deploy never silently fakes
    # publishing, billing, or media generation.
    if settings.meta_mode != "live":
        logger.warning("META_MODE=%s — Facebook/Instagram run in MOCK mode", settings.meta_mode)
    if settings.billing_provider != "stripe":
        logger.warning(
            "BILLING_PROVIDER=%s — billing runs in MOCK mode (upgrades are free)",
            settings.billing_provider,
        )
    if settings.media_provider == "mock":
        logger.warning("MEDIA_PROVIDER=mock — AI reels/video run in MOCK mode")


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
