"""DB-backed onboarding smoke."""

from __future__ import annotations

from httpx import AsyncClient


async def test_onboarding_creates_brand_and_profile(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/onboarding",
        headers=auth_headers,
        json={
            "business_name": "Acme Coffee",
            "website_url": "https://acme.test",
            "industry": "Coffee",
            "goal": "more_leads",
            "platforms": ["facebook", "instagram"],
            "posting_frequency": "few_per_week",
            "monthly_budget": "100_500",
            "biggest_challenge": "No time to post consistently",
            "target_audience": "Local coffee lovers",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["brand"]["name"] == "Acme Coffee"
    assert data["profile"]["goal"] == "more_leads"
    assert data["profile"]["platforms"] == ["facebook", "instagram"]

    # The created brand is listable, and onboarding is retrievable.
    brand_id = data["brand"]["id"]
    latest = await client.get("/api/onboarding", headers=auth_headers)
    assert latest.json()["brand"]["id"] == brand_id


async def test_conversational_onboarding(
    client: AsyncClient, auth_headers: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/onboarding/conversational",
        headers=auth_headers,
        json={"message": "I run a CrossFit gym and want more local members"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["industry"] == "Gym & Fitness"
    assert len(body["content_pillars"]) == 4
    assert body["summary"]
