"""Exercise the LIVE Meta adapter against a simulated Facebook Graph API.

We can't run the real OAuth login (that needs a human + a real Facebook
password), but we can prove the live client sends the correct Graph requests and
parses the responses correctly by mocking the HTTP layer with httpx.MockTransport.
This covers the production connect + publish paths end to end.
"""

from __future__ import annotations

from urllib.parse import parse_qs

import httpx
import pytest

from app.core.config import get_settings
from app.models.social_account import SocialProvider


def _handler(calls: list[httpx.Request]):
    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        path = request.url.path
        if path.endswith("/oauth/access_token"):
            return httpx.Response(200, json={"access_token": "USER_TOKEN"})
        if path.endswith("/me/accounts"):
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "PAGE123",
                            "name": "Glove Cars",
                            "access_token": "PAGE_TOKEN",
                            "instagram_business_account": {
                                "id": "IG123",
                                "username": "glovecars",
                            },
                        }
                    ]
                },
            )
        if path.endswith("/feed"):
            return httpx.Response(200, json={"id": "PAGE123_POST1", "post_id": "PAGE123_POST1"})
        if path.endswith("/photos"):
            return httpx.Response(200, json={"id": "PHOTO1", "post_id": "PAGE123_PHOTOPOST"})
        if path.endswith("/media_publish"):
            return httpx.Response(200, json={"id": "IG_POST1"})
        if path.endswith("/media"):
            return httpx.Response(200, json={"id": "IG_CONTAINER1"})
        return httpx.Response(404, json={"error": {"message": f"unmocked {path}"}})

    return handle


@pytest.fixture
def live(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("META_MODE", "live")
    monkeypatch.setenv("META_APP_ID", "appid")
    monkeypatch.setenv("META_APP_SECRET", "secret")
    monkeypatch.setenv("META_REDIRECT_URI", "https://api.test/callback")
    monkeypatch.setenv("META_GRAPH_VERSION", "v21.0")
    get_settings.cache_clear()
    from app.services.meta import live as livemod

    calls: list[httpx.Request] = []
    real_client = httpx.AsyncClient

    def factory(*args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(_handler(calls))
        return real_client(*args, **kwargs)

    monkeypatch.setattr(livemod.httpx, "AsyncClient", factory)
    yield livemod.LiveMetaClient(), calls
    get_settings.cache_clear()


async def test_connect_exchanges_code_for_page_and_instagram(live) -> None:
    client, _ = live
    accounts = await client.exchange_code_for_accounts("AUTH_CODE")

    fb = [a for a in accounts if a.provider == SocialProvider.facebook_page]
    ig = [a for a in accounts if a.provider == SocialProvider.instagram]
    assert len(fb) == 1 and len(ig) == 1
    assert fb[0].external_id == "PAGE123"
    assert fb[0].access_token == "PAGE_TOKEN"
    assert ig[0].ig_user_id == "IG123"
    assert "glovecars" in ig[0].display_name


async def test_publish_facebook_text_post(live) -> None:
    client, calls = live
    result = await client.publish_post(
        provider=SocialProvider.facebook_page,
        external_id="PAGE123",
        access_token="PAGE_TOKEN",
        body="Hello world",
        media_urls=[],
    )
    assert result.external_post_id == "PAGE123_POST1"
    feed = [c for c in calls if c.url.path.endswith("/feed")]
    assert len(feed) == 1
    form = parse_qs(feed[0].content.decode())
    assert form["message"] == ["Hello world"]
    assert form["access_token"] == ["PAGE_TOKEN"]


async def test_publish_facebook_image_post(live) -> None:
    client, calls = live
    result = await client.publish_post(
        provider=SocialProvider.facebook_page,
        external_id="PAGE123",
        access_token="PAGE_TOKEN",
        body="Nice car",
        media_urls=["https://cdn.test/car.jpg"],
    )
    # A photo post returns post_id, preferred over the raw id.
    assert result.external_post_id == "PAGE123_PHOTOPOST"
    photos = [c for c in calls if c.url.path.endswith("/photos")]
    assert len(photos) == 1
    form = parse_qs(photos[0].content.decode())
    assert form["url"] == ["https://cdn.test/car.jpg"]
    assert form["caption"] == ["Nice car"]


async def test_publish_instagram_image_two_step(live) -> None:
    client, calls = live
    result = await client.publish_post(
        provider=SocialProvider.instagram,
        external_id="IG123",
        ig_user_id="IG123",
        access_token="PAGE_TOKEN",
        body="On the lot",
        media_urls=["https://cdn.test/car.jpg"],
    )
    assert result.external_post_id == "IG_POST1"
    # Instagram is a two-step flow: create container, then publish it.
    paths = [c.url.path for c in calls]
    assert any(p.endswith("/media") for p in paths)
    assert any(p.endswith("/media_publish") for p in paths)
    publish = [c for c in calls if c.url.path.endswith("/media_publish")][0]
    assert parse_qs(publish.content.decode())["creation_id"] == ["IG_CONTAINER1"]


async def test_instagram_requires_media(live) -> None:
    from app.services.meta.base import MetaError

    client, _ = live
    with pytest.raises(MetaError):
        await client.publish_post(
            provider=SocialProvider.instagram,
            external_id="IG123",
            ig_user_id="IG123",
            access_token="PAGE_TOKEN",
            body="text only",
            media_urls=[],
        )
