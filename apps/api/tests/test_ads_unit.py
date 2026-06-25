"""Unit tests for ad creative generation + recommendations (no DB)."""

from __future__ import annotations

from types import SimpleNamespace

from app.models.ads import CreativeStatus
from app.services.ads import generate_creatives, recommendations


async def test_generate_creatives_count_capped() -> None:
    brand = SimpleNamespace(name="Acme Coffee")
    ideas = await generate_creatives(brand, "fall menu", count=15)
    assert len(ideas) == 15
    assert all(i.headline for i in ideas)
    # Capped at 20.
    assert len(await generate_creatives(brand, "x", count=99)) == 20


def test_recommendations_scale_and_pause() -> None:
    def creative(ctr: float):
        return SimpleNamespace(
            id="c-" + str(ctr),
            status=CreativeStatus.active,
            metrics_json={"ctr": ctr},
        )

    campaign = SimpleNamespace(
        creatives=[creative(5.0), creative(0.2), creative(2.0), creative(2.0)]
    )
    out = recommendations(campaign)
    actions = {r["action"] for r in out["recommendations"]}
    assert "scale" in actions  # the 5.0% CTR creative
    assert "pause" in actions  # the 0.2% CTR creative
    assert out["summary"]


def test_recommendations_without_metrics() -> None:
    campaign = SimpleNamespace(creatives=[SimpleNamespace(metrics_json={})])
    out = recommendations(campaign)
    assert out["recommendations"] == []
