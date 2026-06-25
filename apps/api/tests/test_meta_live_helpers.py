"""Unit tests for the live Meta client's pure parsing/time helpers (no network)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.services.meta.live import LiveMetaClient, _minutes_ago


def test_latest_metric_values_flattens_and_sums() -> None:
    payload = {
        "data": [
            {"name": "page_impressions", "values": [{"value": 10}, {"value": 42}]},
            {"name": "page_post_engagements", "values": [{"value": 7}]},
            # dict-breakdown metric → summed
            {"name": "page_fans_by_country", "values": [{"value": {"US": 3, "CA": 2}}]},
            # malformed entries are ignored / coerced
            {"name": "bad", "values": []},
            {"name": "nonnumeric", "values": [{"value": "oops"}]},
        ]
    }
    out = LiveMetaClient._latest_metric_values(payload)
    assert out["page_impressions"] == 42  # latest value wins
    assert out["page_post_engagements"] == 7
    assert out["page_fans_by_country"] == 5  # 3 + 2
    assert "bad" not in out
    assert out["nonnumeric"] == 0


def test_day_window_is_a_24h_utc_bucket() -> None:
    since, until = LiveMetaClient._day_window(0)
    assert until - since == 86_400
    # since must align to UTC midnight.
    assert datetime.fromtimestamp(since, UTC).hour == 0


def test_day_window_offset_goes_back_in_time() -> None:
    today_since, _ = LiveMetaClient._day_window(0)
    yday_since, _ = LiveMetaClient._day_window(1)
    assert today_since - yday_since == 86_400


def test_minutes_ago_parses_graph_timestamp() -> None:
    now = datetime(2026, 6, 25, 12, 0, 0, tzinfo=UTC)
    assert _minutes_ago("2026-06-25T11:30:00+0000", now) == 30
    assert _minutes_ago(None, now) == 0
    assert _minutes_ago("not-a-date", now) == 0
    # Future timestamps clamp to 0, never negative.
    assert _minutes_ago("2026-06-25T13:00:00+0000", now) == 0
