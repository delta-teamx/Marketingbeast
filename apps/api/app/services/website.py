"""Fetch and strip a website to plain text (for niche detection).

Uses httpx (already a dependency) and a stdlib HTML parser — no heavy scraping
deps. Reusable by the Phase 2 audit. Respects a short timeout and caps length.
"""

from __future__ import annotations

import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlsplit

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

_MAX_CHARS = 8000
_MAX_BYTES = 2_000_000  # don't download more than ~2MB of HTML
_MAX_REDIRECTS = 4
_SKIP_TAGS = {"script", "style", "noscript", "template", "svg"}


def host_is_public(host: str) -> bool:
    """True only if every IP `host` resolves to is a public, routable address.

    Blocks SSRF: loopback, private (RFC1918), link-local (incl. the cloud
    metadata endpoint 169.254.169.254), and other reserved ranges. Resolution
    failure or an empty host is treated as unsafe.
    """
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if not ip.is_global or ip.is_reserved:
            return False
    return bool(infos)


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
    """Return visible text from a URL, or "" on any failure (never raises).

    User-supplied URLs are fetched server-side, so we guard against SSRF: every
    hop (including redirects) must resolve to a public IP. Redirects are followed
    manually so a public URL can't bounce us to an internal address.
    """
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    try:
        async with httpx.AsyncClient(
            timeout=10, follow_redirects=False, headers={"User-Agent": "PresenceBot/0.1"}
        ) as client:
            for _ in range(_MAX_REDIRECTS + 1):
                host = urlsplit(url).hostname or ""
                if not host_is_public(host):
                    logger.warning("blocked non-public host for %s", url)
                    return ""
                resp = await client.get(url)
                if resp.is_redirect and resp.headers.get("location"):
                    url = str(resp.url.join(resp.headers["location"]))
                    continue
                resp.raise_for_status()
                return html_to_text(resp.text[:_MAX_BYTES])
            logger.warning("too many redirects for %s", url)
            return ""
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("failed to fetch %s: %s", url, exc)
        return ""
