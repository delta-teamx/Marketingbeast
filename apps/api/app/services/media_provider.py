"""AI media generation provider adapter (video/reels).

One interface, swappable providers (brief §6.5). MEDIA_PROVIDER selects: "mock"
(default; renders complete on the first poll, no creds), or a real provider
(runway / creatify / heygen) wired with MEDIA_API_KEY + App access.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from app.core.config import get_settings


@dataclass
class RenderBrief:
    script: str
    storyboard: list[dict[str, Any]] = field(default_factory=list)
    product_url: str | None = None
    style: str = "ugc"  # bias toward UGC-style, slightly imperfect clips


@dataclass
class RenderStatus:
    external_job_id: str
    ready: bool
    asset_url: str | None = None
    failed: bool = False


@runtime_checkable
class MediaProvider(Protocol):
    name: str

    def start_render(self, brief: RenderBrief) -> str:
        """Kick off an async render, return the provider job id."""
        ...

    def poll_render(self, external_job_id: str) -> RenderStatus:
        """Check render status; mock completes on the first poll."""
        ...


class MockMediaProvider:
    name = "mock"

    def start_render(self, brief: RenderBrief) -> str:
        return f"mock_render_{uuid.uuid4().hex[:12]}"

    def poll_render(self, external_job_id: str) -> RenderStatus:
        # Deterministic: the mock always completes immediately.
        return RenderStatus(
            external_job_id=external_job_id,
            ready=True,
            asset_url=f"https://mock.local/renders/{external_job_id}.mp4",
        )


class StubMediaProvider:
    """Placeholder for a real provider (runway/creatify/heygen)."""

    def __init__(self, name: str) -> None:
        self.name = name

    def start_render(self, brief: RenderBrief) -> str:  # pragma: no cover - live path
        raise NotImplementedError(f"{self.name} provider lands with MEDIA_API_KEY + access")

    def poll_render(self, external_job_id: str) -> RenderStatus:  # pragma: no cover
        raise NotImplementedError(f"{self.name} provider lands with MEDIA_API_KEY + access")


def get_media_provider() -> MediaProvider:
    provider = get_settings().media_provider
    if provider in ("", "mock"):
        return MockMediaProvider()
    return StubMediaProvider(provider)
