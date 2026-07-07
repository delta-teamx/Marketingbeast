"""AI post-image generation provider.

Claude/Anthropic is text-only and cannot generate images, so image creation is a
separate provider (mirroring media_provider.py). The content engine has Claude
write an art-direction *prompt*; this provider renders it to a public image URL
that gets attached to the post's media_urls and published alongside the caption.

IMAGE_PROVIDER selects: "mock" (default; deterministic placeholder URL, no key)
or "openai" (OpenAI Images, requires IMAGE_API_KEY).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ImageBrief:
    prompt: str
    brand_name: str = ""
    # Square 1:1 is the safe default for both Facebook and Instagram feed posts.
    size: str = "1024x1024"


@runtime_checkable
class ImageProvider(Protocol):
    name: str

    async def generate(self, brief: ImageBrief) -> str | None:
        """Render an image for the brief and return a public URL (or None)."""
        ...


class MockImageProvider:
    """Deterministic placeholder image, no key/network at generate time.

    Returns a stable public URL derived from the prompt so the same brief always
    maps to the same image — deterministic for tests and demos, and (because it's
    a real reachable URL) publishable even through the live Meta adapter.
    """

    name = "mock"

    async def generate(self, brief: ImageBrief) -> str | None:
        seed = hashlib.sha1(brief.prompt.encode()).hexdigest()[:16]
        w, _, h = brief.size.partition("x")
        w = w or "1024"
        h = h or "1024"
        return f"https://picsum.photos/seed/{seed}/{w}/{h}"


class OpenAIImageProvider:
    """OpenAI Images (IMAGE_PROVIDER=openai).

    Implemented against the documented Images API. Not exercised by the test
    suite (which uses the mock) — verify with a real key before production. Note:
    OpenAI returns a short-lived URL; for scheduled posts that publish later,
    persist the image to your own storage. Immediate publishes work as-is.
    """

    name = "openai"

    def __init__(self) -> None:
        s = get_settings()
        self._base = s.image_base_url.rstrip("/")
        self._model = s.image_model
        self._key = s.image_api_key

    async def generate(self, brief: ImageBrief) -> str | None:
        if not self._key:
            raise RuntimeError("IMAGE_API_KEY is required for the openai image provider")
        prompt = brief.prompt
        if brief.brand_name:
            prompt = f"{prompt}\nBrand: {brief.brand_name}. No text or logos in the image."
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base}/images/generations",
                headers={"Authorization": f"Bearer {self._key}"},
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "n": 1,
                    "size": brief.size,
                },
            )
        if resp.status_code >= 400:
            raise RuntimeError(f"OpenAI image {resp.status_code}: {resp.text}")
        data = resp.json().get("data", [])
        if not data:
            return None
        # The API returns either a hosted url or base64 (b64_json) depending on model.
        first = data[0]
        if first.get("url"):
            return str(first["url"])
        if first.get("b64_json"):
            return f"data:image/png;base64,{first['b64_json']}"
        return None


def get_image_provider() -> ImageProvider:
    provider = get_settings().image_provider
    if provider in ("", "mock"):
        return MockImageProvider()
    if provider == "openai":
        return OpenAIImageProvider()
    # Unknown provider name — fail safe to mock rather than crash content gen.
    logger.warning("unknown IMAGE_PROVIDER=%s; falling back to mock", provider)
    return MockImageProvider()
