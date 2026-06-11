"""Fetch and strip a website to plain text (for niche detection).

Uses httpx (already a dependency) and a stdlib HTML parser — no heavy scraping
deps. Reusable by the Phase 2 audit. Respects a short timeout and caps length.
"""

from __future__ import annotations

from html.parser import HTMLParser

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

_MAX_CHARS = 8000
_SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._chunks.append(text)

    @property
    def text(self) -> str:
        return " ".join(self._chunks)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text[:_MAX_CHARS]


async def fetch_site_text(url: str) -> str:
    """Return visible text from a URL, or "" on any failure (never raises)."""
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    try:
        async with httpx.AsyncClient(
            timeout=10, follow_redirects=True, headers={"User-Agent": "PresenceBot/0.1"}
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return html_to_text(resp.text)
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("failed to fetch %s: %s", url, exc)
        return ""
