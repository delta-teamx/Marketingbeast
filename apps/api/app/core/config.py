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

    # Redis / Celery
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="REDIS_URL")

    # Token encryption at rest (Fernet) — used for social OAuth tokens (Phase 1+).
    fernet_key: str = Field(default="", alias="FERNET_KEY")

    # LLM provider
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    llm_model: str = Field(default="claude-sonnet-4-6", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
