"""Unit tests for lead intent scoring (no DB)."""

from __future__ import annotations

from app.services.inbox import score_intent


def test_buyer_intent_scores_high() -> None:
    assert score_intent("How much is it? I'd like to buy today") >= 40
    assert score_intent("Do you have it in stock? interested!") >= 40


def test_casual_comment_scores_low() -> None:
    assert score_intent("Nice photo 🔥") < 40
    assert score_intent("Love your page!") < 40
