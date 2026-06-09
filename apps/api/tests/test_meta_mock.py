"""Unit tests for the mock Meta client + OAuth state (no DB required)."""

from __future__ import annotations

import jwt
import pytest

from app.models.social_account import SocialProvider
from app.services.meta.mock import MockMetaClient
from app.services.oauth_state import decode_state, encode_state


async def test_mock_exchange_returns_page_and_ig() -> None:
    accounts = await MockMetaClient().exchange_code_for_accounts("abc123")
    providers = {a.provider for a in accounts}
    assert providers == {SocialProvider.facebook_page, SocialProvider.instagram}
    ig = next(a for a in accounts if a.provider == SocialProvider.instagram)
    assert ig.ig_user_id is not None


async def test_mock_publish_returns_post_id() -> None:
    result = await MockMetaClient().publish_post(
        provider=SocialProvider.facebook_page,
        external_id="mock_page_1",
        access_token="t",
        body="hello",
        media_urls=[],
    )
    assert result.external_post_id.startswith("mock_post_")


def test_oauth_state_roundtrip() -> None:
    token = encode_state(brand_id="b1", user_id="u1")
    decoded = decode_state(token)
    assert decoded == {"brand_id": "b1", "user_id": "u1"}


def test_oauth_state_rejects_wrong_purpose() -> None:
    from app.core.config import get_settings

    bad = jwt.encode({"purpose": "nope"}, get_settings().supabase_jwt_secret, algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError):
        decode_state(bad)
