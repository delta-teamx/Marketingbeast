"""Shared pytest fixtures.

Test env vars are set BEFORE the app config is imported so settings pick them up.
DB-backed tests connect to DATABASE_URL (a pgvector Postgres in CI / Supabase
locally) and skip cleanly if no database is reachable.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import AsyncGenerator

# --- Test environment (must precede any app import) ---
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-at-least-32-characters-long!!")
os.environ.setdefault("FERNET_KEY", "SjaxcdlQ7S94Jw19vRzrRIeRJS0IvzNPIVFllzUMI-w=")
os.environ.setdefault("API_ENV", "test")

import jwt  # noqa: E402
import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()


def make_token(user_id: str, email: str = "dev@example.com") -> str:
    """Forge a Supabase-style access token signed with the test secret."""
    settings = get_settings()
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, settings.supabase_jwt_secret, algorithm="HS256")


@pytest.fixture
def user_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def auth_headers(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user_id)}"}


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh schema for DB-backed tests; skip if DB unreachable."""
    from app.db.base import Base
    from app.db.session import AsyncSessionLocal, engine

    # pytest-asyncio gives each test a fresh event loop, but the app's async
    # engine pools connections — a pooled asyncpg connection reused on a new loop
    # raises MissingGreenlet. Dispose around each test so connections never cross
    # event loops.
    await engine.dispose()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # pragma: no cover - infra dependent
        pytest.skip(f"database not available: {exc}")

    async with AsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client bound to the app, using the test DB schema."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
