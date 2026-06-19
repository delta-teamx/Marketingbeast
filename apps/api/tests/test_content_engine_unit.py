"""Unit tests for the content engine (no DB)."""

from __future__ import annotations

from types import SimpleNamespace

from app.models.content import ContentType
from app.services.content_engine import best_times, generate_ideas, repurpose


def _brand() -> SimpleNamespace:
    return SimpleNamespace(
        name="Acme Coffee",
        industry_vertical="Coffee",
        niche_summary="specialty coffee",
        niche_keywords=["coffee", "espresso"],
        voice_profile_json=None,
    )


def test_best_times_cover_the_week() -> None:
    bt = best_times()
    assert set(bt.keys()) == {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
    assert all(len(v) >= 1 for v in bt.values())


async def test_generate_ideas_mock_shape() -> None:
    ideas = await generate_ideas(_brand(), "fall menu", count=7)
    assert len(ideas) == 7
    assert all(i.body for i in ideas)
    assert all(i.hashtags for i in ideas)
    assert all(i.suggested_time for i in ideas)


def test_repurpose_makes_three_formats() -> None:
    variants = repurpose("Our cold brew is back")
    types = {v.content_type for v in variants}
    assert types == {ContentType.post, ContentType.reel, ContentType.story}
