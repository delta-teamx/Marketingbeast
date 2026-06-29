"""The live Meta adapter builds a correct Facebook OAuth dialog URL.

This is the production connect path (META_MODE=live): the URL must carry the
configured app id, the exact redirect URI, and every scope the app needs for
App Review — so a misconfiguration is caught here, not at a user's failed login.
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

import pytest

from app.core.config import get_settings


@pytest.fixture
def live_meta(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("META_MODE", "live")
    monkeypatch.setenv("META_APP_ID", "1234567890")
    monkeypatch.setenv("META_APP_SECRET", "shh-secret")
    monkeypatch.setenv(
        "META_REDIRECT_URI",
        "https://marketingbeast.onrender.com/api/integrations/meta/oauth/callback",
    )
    monkeypatch.setenv("META_GRAPH_VERSION", "v21.0")
    get_settings.cache_clear()
    from app.services.meta.live import LiveMetaClient

    yield LiveMetaClient()
    get_settings.cache_clear()


def test_oauth_url_has_app_id_redirect_and_state(live_meta) -> None:
    url = live_meta.build_oauth_url(state="signed-state-token")
    parts = urlsplit(url)
    assert parts.netloc == "www.facebook.com"
    assert parts.path == "/v21.0/dialog/oauth"
    q = parse_qs(parts.query)
    assert q["client_id"] == ["1234567890"]
    assert q["redirect_uri"] == [
        "https://marketingbeast.onrender.com/api/integrations/meta/oauth/callback"
    ]
    assert q["state"] == ["signed-state-token"]
    assert q["response_type"] == ["code"]


def test_oauth_url_requests_every_required_scope(live_meta) -> None:
    from app.services.meta.live import OAUTH_SCOPES

    url = live_meta.build_oauth_url(state="x")
    scopes = parse_qs(urlsplit(url).query)["scope"][0].split(",")
    for required in (
        "pages_show_list",
        "pages_manage_posts",
        "instagram_basic",
        "instagram_content_publish",
        "business_management",
    ):
        assert required in scopes
    assert set(scopes) == set(OAUTH_SCOPES)
