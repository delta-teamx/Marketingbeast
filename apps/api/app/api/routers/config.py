"""Public feature-flag config for the web app.

Exposes only which features are live vs. still in demo/coming-soon state, so the
frontend can render the right UI (e.g. a 'coming soon' Ads Manager in live mode)
without hard-coding backend config. No secrets are returned.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["config"])


@router.get("/api/config")
async def app_config() -> dict[str, bool]:
    settings = get_settings()
    # The Ads Manager's real Meta Marketing API path isn't implemented yet, so it
    # only functions against the mock adapter (demo mode). In live mode it's shown
    # as 'coming soon' rather than a connect button that can't work.
    #
    # Reels/video needs a real render provider (MEDIA_PROVIDER != mock); until one
    # is configured it's shown as 'coming soon' too.
    return {
        "ads_enabled": settings.meta_mode == "mock",
        "media_enabled": settings.media_provider != "mock",
    }
