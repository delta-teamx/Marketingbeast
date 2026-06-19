"""Meta Marketing API client (ads) — mock + live behind one interface.

Mirrors the graph client: META_MODE=mock (default) uses an in-process fake so
campaign launch + insights are testable with no creds; META_MODE=live targets
the real Marketing API (stub pending ads_management + App Review).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.core.config import get_settings


@dataclass
class AdMetrics:
    impressions: int
    clicks: int
    spend: float
    conversions: int

    @property
    def ctr(self) -> float:
        return round(self.clicks / self.impressions * 100, 2) if self.impressions else 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "impressions": self.impressions,
            "clicks": self.clicks,
            "spend": round(self.spend, 2),
            "conversions": self.conversions,
            "ctr": self.ctr,
        }


@runtime_checkable
class AdsClient(Protocol):
    def create_campaign(self, *, account_external_id: str, name: str, objective: str) -> str: ...
    def create_creative(self, *, campaign_external_id: str, headline: str) -> str: ...
    def fetch_insights(self, *, external_id: str) -> AdMetrics: ...


def _seed(text: str) -> int:
    return sum(ord(c) for c in text) or 1


class MockAdsClient:
    def create_campaign(self, *, account_external_id: str, name: str, objective: str) -> str:
        return f"mock_camp_{uuid.uuid4().hex[:10]}"

    def create_creative(self, *, campaign_external_id: str, headline: str) -> str:
        return f"mock_ad_{uuid.uuid4().hex[:10]}"

    def fetch_insights(self, *, external_id: str) -> AdMetrics:
        s = _seed(external_id)
        impressions = 1000 + s % 9000
        clicks = max(1, int(impressions * (0.5 + s % 40 / 10) / 100))  # ~0.5%–4.5% CTR
        spend = round(impressions / 1000 * (5 + s % 10), 2)
        conversions = max(0, clicks // (3 + s % 5))
        return AdMetrics(impressions, clicks, spend, conversions)


class LiveAdsClient:
    def __init__(self) -> None:
        s = get_settings()
        self._app_id = s.meta_app_id
        self._app_secret = s.meta_app_secret

    def create_campaign(self, *, account_external_id: str, name: str, objective: str) -> str:
        raise NotImplementedError("Live Marketing API lands with ads_management + App Review")

    def create_creative(self, *, campaign_external_id: str, headline: str) -> str:
        raise NotImplementedError("Live Marketing API lands with ads_management + App Review")

    def fetch_insights(self, *, external_id: str) -> AdMetrics:
        return AdMetrics(0, 0, 0.0, 0)


def get_ads_client() -> AdsClient:
    if get_settings().meta_mode == "live":
        return LiveAdsClient()
    return MockAdsClient()
