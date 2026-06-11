"""Unit tests for audit scoring (no DB)."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.audit import build_sections, grade_from_score


def test_grade_mapping() -> None:
    assert grade_from_score(95) == "A"
    assert grade_from_score(82) == "B"
    assert grade_from_score(71) == "C"
    assert grade_from_score(61) == "D"
    assert grade_from_score(40) == "F"


def test_sections_reward_completeness_and_breadth() -> None:
    rich = SimpleNamespace(
        website_url="https://x.test",
        industry_vertical="Coffee",
        niche_summary="specialty coffee",
        logo_url="https://x.test/logo.png",
    )
    bare = SimpleNamespace(
        website_url=None, industry_vertical=None, niche_summary=None, logo_url=None
    )

    rich_sections = build_sections(
        brand=rich, providers={"facebook_page", "instagram"}, content_count=10, has_site_text=True
    )
    bare_sections = build_sections(
        brand=bare, providers=set(), content_count=0, has_site_text=False
    )

    def score(sections, key):
        return next(s["score"] for s in sections if s["key"] == key)

    assert score(rich_sections, "profile") > score(bare_sections, "profile")
    assert score(rich_sections, "breadth") > score(bare_sections, "breadth")
    assert score(rich_sections, "consistency") > score(bare_sections, "consistency")
    assert all(0 <= s["score"] <= 100 for s in rich_sections + bare_sections)
