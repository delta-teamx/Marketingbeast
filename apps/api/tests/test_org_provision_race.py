"""Concurrency test: a brand-new user's first page load fires several API calls
in parallel. Personal-org provisioning must be race-safe — the user must never
get a 500 from a duplicate-org insert, and must end up with exactly one org.
"""

from __future__ import annotations

import asyncio

from httpx import AsyncClient
from sqlalchemy import func, select

from app.db.session import AsyncSessionLocal
from app.models.organization import Organization
from app.services.provisioning import ensure_personal_org


async def test_concurrent_me_provisions_single_org(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    # Simulate the dashboard's parallel first-load calls to /api/auth/me.
    results = await asyncio.gather(
        *[client.get("/api/auth/me", headers=auth_headers) for _ in range(6)]
    )
    assert all(r.status_code == 200 for r in results), [r.status_code for r in results]

    orgs = await client.get("/api/organizations", headers=auth_headers)
    assert orgs.status_code == 200
    assert len(orgs.json()) == 1


async def test_ensure_personal_org_idempotent_across_sessions(
    db: object, user_id: str
) -> None:
    """Two independent sessions provisioning concurrently yield one org, no error."""
    from app.core.security import AuthenticatedUser

    user = AuthenticatedUser(id=user_id, email="race@example.com", role="authenticated")

    async def provision() -> None:
        async with AsyncSessionLocal() as session:
            await ensure_personal_org(session, user)

    await asyncio.gather(*[provision() for _ in range(6)])

    async with AsyncSessionLocal() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(Organization)
            .where(Organization.is_personal.is_(True))
        )
    assert count == 1
