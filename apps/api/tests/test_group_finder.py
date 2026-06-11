"""Unit tests for niche detection + group suggestions (mock mode, no DB)."""

from __future__ import annotations

from app.services.group_finder import (
    NicheProfile,
    detect_niche,
    suggest_groups,
)
from app.services.website import html_to_text


def test_html_to_text_strips_scripts_and_tags() -> None:
    html = "<html><head><style>.a{color:red}</style></head><body><h1>Acme Coffee</h1>"
    html += "<script>alert(1)</script><p>Best roast in town</p></body></html>"
    text = html_to_text(html)
    assert "Acme Coffee" in text
    assert "Best roast in town" in text
    assert "alert(1)" not in text
    assert "color:red" not in text


async def test_detect_niche_mock_uses_keywords() -> None:
    niche = await detect_niche(
        brand_name="Acme Coffee",
        website_text="Specialty coffee roastery serving espresso and cold brew",
        vertical=None,
    )
    assert niche.category
    assert len(niche.keywords) >= 1


async def test_suggest_groups_mock_is_ranked_and_bounded() -> None:
    niche = NicheProfile(category="Coffee", summary="x", keywords=["coffee", "espresso"])
    groups = await suggest_groups(brand_name="Acme Coffee", niche=niche)
    assert len(groups) >= 3
    for g in groups:
        assert 0 <= g.relevance_score <= 100
        assert 0 <= g.lead_quality_score <= 100
        assert g.search_keyword
    # Highest relevance first.
    scores = [g.relevance_score for g in groups]
    assert scores == sorted(scores, reverse=True)
