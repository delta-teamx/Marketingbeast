"""Unit tests for vertical tuning (no DB)."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.content_engine import generate_ideas
from app.services.verticals import resolve_vertical, vertical_profile


def test_resolve_vertical_maps_keywords() -> None:
    assert resolve_vertical("I run a CrossFit gym for locals") == "gym"
    assert resolve_vertical("used car dealership downtown") == "auto"
    assert resolve_vertical("cozy italian restaurant") == "restaurant"
    assert resolve_vertical("real estate broker") == "real_estate"
    assert resolve_vertical("we make industrial widgets") == "default"
    assert resolve_vertical(None) == "default"


def test_vertical_profile_has_tuning() -> None:
    p = vertical_profile("gym")
    assert p["label"] == "Gym & Fitness"
    assert p["angles"] and p["hashtags"] and p["offers"]


async def test_generated_content_is_vertical_tuned() -> None:
    brand = SimpleNamespace(
        name="Iron Gym",
        industry_vertical="gym",
        niche_summary="fitness studio",
        niche_keywords=["fitness"],
        voice_profile_json=None,
    )
    ideas = await generate_ideas(brand, "new class launch", count=4)
    # The gym signature hashtag flows through.
    assert any("#fitness" in i.hashtags for i in ideas)
