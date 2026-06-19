"""SSRF guard for the user-supplied website fetcher: only public hosts allowed."""

from __future__ import annotations

import pytest

from app.services.website import fetch_site_text, host_is_public


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "localhost",
        "0.0.0.0",
        "169.254.169.254",  # cloud metadata endpoint
        "10.0.0.5",
        "192.168.1.1",
        "172.16.0.1",
        "::1",
        "",
        "no-such-host.invalid",
    ],
)
def test_internal_and_bad_hosts_blocked(host: str) -> None:
    assert host_is_public(host) is False


@pytest.mark.parametrize("host", ["8.8.8.8", "1.1.1.1"])
def test_public_ips_allowed(host: str) -> None:
    assert host_is_public(host) is True


async def test_fetch_blocks_internal_url_without_request() -> None:
    # Must return "" without ever issuing the request to an internal address.
    assert await fetch_site_text("http://169.254.169.254/latest/meta-data/") == ""
    assert await fetch_site_text("http://localhost:8000/admin") == ""
