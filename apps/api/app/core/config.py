"""Application settings, loaded from environment variables.

Secrets are NEVER hardcoded. See `.env.example` for the full list.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    api_env: str = Field(default="development", alias="API_ENV")
    api_cors_origins: str = Field(default="http://localhost:3000", alias="API_CORS_ORIGINS")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres",
        alias="DATABASE_URL",
    )

    # Supabase Auth — used to validate access tokens (HS256).
    supabase_jwt_secret: str = Field(
        default="super-secret-jwt-token-with-at-least-32-characters-long",
        alias="SUPABASE_JWT_SECRET",
    )
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    # Auth mode: "supabase" (default) validates Supabase JWTs; "dev" uses a single
    # fixed demo user (no Supabase needed) — for local demos only.
    auth_mode: str = Field(default="supabase", alias="AUTH_MODE")

    # Redis / Celery
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="REDIS_URL")

    # Token encryption at rest (Fernet) — used for social OAuth tokens (Phase 1+).
    fernet_key: str = Field(default="", alias="FERNET_KEY")

    # LLM provider. "auto" (default) uses Claude when ANTHROPIC_API_KEY is set,
    # otherwise the deterministic mock. Set to "anthropic" or "mock" to force.
    llm_provider: str = Field(default="auto", alias="LLM_PROVIDER")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    llm_model: str = Field(default="claude-sonnet-4-6", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2048, alias="LLM_MAX_TOKENS")

    # Meta (Facebook / Instagram) — Tier A publishing.
    # mode "mock" (default) uses an in-process fake; "live" hits the Graph API.
    meta_mode: str = Field(default="mock", alias="META_MODE")
    meta_app_id: str = Field(default="", alias="META_APP_ID")
    meta_app_secret: str = Field(default="", alias="META_APP_SECRET")
    meta_redirect_uri: str = Field(
        default="http://localhost:8000/api/integrations/meta/oauth/callback",
        alias="META_REDIRECT_URI",
    )
    meta_graph_version: str = Field(default="v21.0", alias="META_GRAPH_VERSION")
    # Public base URL the OAuth dialog redirects the browser back to (the web app).
    web_app_url: str = Field(default="http://localhost:3000", alias="WEB_APP_URL")

    # Frequency (seconds) of the Celery beat job that publishes due content.
    publish_poll_seconds: float = Field(default=60.0, alias="PUBLISH_POLL_SECONDS")

    # AI media generation (video/reels). "mock" (default) or a provider name
    # (e.g. "creatify"). Creatify auth needs BOTH an API id and key.
    media_provider: str = Field(default="mock", alias="MEDIA_PROVIDER")
    media_api_id: str = Field(default="", alias="MEDIA_API_ID")
    media_api_key: str = Field(default="", alias="MEDIA_API_KEY")
    media_base_url: str = Field(default="https://api.creatify.ai", alias="MEDIA_BASE_URL")
    # Credits charged per generated video, and starter credits per new org.
    video_cost_credits: int = Field(default=10, alias="VIDEO_COST_CREDITS")
    starter_credits: int = Field(default=100, alias="STARTER_CREDITS")

    # AI post-image generation (Claude writes the art-direction prompt; an image
    # model renders it — Claude/Anthropic cannot generate images itself).
    # "mock" (default) returns a deterministic placeholder image URL; "openai"
    # renders with OpenAI Images. Requires IMAGE_API_KEY for the live provider.
    image_provider: str = Field(default="mock", alias="IMAGE_PROVIDER")
    image_api_key: str = Field(default="", alias="IMAGE_API_KEY")
    image_model: str = Field(default="gpt-image-1", alias="IMAGE_MODEL")
    image_base_url: str = Field(default="https://api.openai.com/v1", alias="IMAGE_BASE_URL")

    # Real Facebook-group discovery via a web-search API (Meta has no Groups API).
    # "none" (default) keeps suggestions AI-advisory; "tavily" finds real public
    # facebook.com/groups pages. Requires GROUP_SEARCH_API_KEY for a live provider.
    group_search_provider: str = Field(default="none", alias="GROUP_SEARCH_PROVIDER")
    group_search_api_key: str = Field(default="", alias="GROUP_SEARCH_API_KEY")
    group_search_base_url: str = Field(
        default="https://api.tavily.com", alias="GROUP_SEARCH_BASE_URL"
    )

    # Billing (Stripe). "mock" (default) applies upgrades instantly for dev/tests;
    # "stripe" uses Checkout + webhooks.
    billing_provider: str = Field(default="mock", alias="BILLING_PROVIDER")
    stripe_secret_key: str = Field(default="", alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: str = Field(default="", alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_growth: str = Field(default="", alias="STRIPE_PRICE_GROWTH")
    stripe_price_agency: str = Field(default="", alias="STRIPE_PRICE_AGENCY")
    billing_success_url: str = Field(
        default="http://localhost:3000/dashboard?upgraded=1", alias="BILLING_SUCCESS_URL"
    )
    billing_cancel_url: str = Field(
        default="http://localhost:3000/pricing", alias="BILLING_CANCEL_URL"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
