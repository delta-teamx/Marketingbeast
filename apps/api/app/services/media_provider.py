"""AI media generation provider adapter (video/reels).

One interface, swappable providers (brief §6.5). MEDIA_PROVIDER selects: "mock"
(default; renders complete on the first poll, no creds), or a real provider
(runway / creatify / heygen) wired with MEDIA_API_KEY + App access.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import httpx

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


# Creatify "link-to-video" provider (MEDIA_PROVIDER=creatify).
#
# Like app/services/meta/live.py, this is implemented against Creatify's
# published API and is ready for real credentials, but is NOT exercised by the
# test suite (which uses the mock). The exact endpoint paths and response field
# names below follow Creatify's documented API and SHOULD BE VERIFIED against the
# current Creatify API docs with real credentials before production use.
class CreatifyMediaProvider:
    name = "creatify"

    def __init__(self) -> None:
        s = get_settings()
        self._base = s.media_base_url.rstrip("/")
        self._headers = {
            "X-API-ID": s.media_api_id,
            "X-API-KEY": s.media_api_key,
        }

    def start_render(self, brief: RenderBrief) -> str:
        if not brief.product_url:
            raise RuntimeError("Creatify requires a product_url for link-to-video")
        with httpx.Client(timeout=60, headers=self._headers) as client:
            resp = client.post(
                f"{self._base}/api/link_to_videos/",
                json={"link": brief.product_url, "name": brief.script[:64] or "reel"},
            )
        if resp.status_code >= 400:
            raise RuntimeError(f"Creatify {resp.status_code}: {resp.text}")
        return str(resp.json()["id"])

    def poll_render(self, external_job_id: str) -> RenderStatus:
        # Never raise in poll: an HTTP/transport error maps to a failed render so
        # the job loop can record it rather than crash the poller.
        try:
            with httpx.Client(timeout=30, headers=self._headers) as client:
                resp = client.get(f"{self._base}/api/link_to_videos/{external_job_id}/")
            if resp.status_code >= 400:
                return RenderStatus(external_job_id=external_job_id, ready=False, failed=True)
            data = resp.json()
        except httpx.HTTPError:
            return RenderStatus(external_job_id=external_job_id, ready=False, failed=True)

        status = data.get("status")
        if status == "done":
            asset_url = data.get("video_output") or data.get("output") or data.get("video_url")
            return RenderStatus(external_job_id=external_job_id, ready=True, asset_url=asset_url)
        if status in ("error", "failed"):
            return RenderStatus(external_job_id=external_job_id, ready=False, failed=True)
        return RenderStatus(external_job_id=external_job_id, ready=False)


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
    if provider == "creatify":
        return CreatifyMediaProvider()
    return StubMediaProvider(provider)
