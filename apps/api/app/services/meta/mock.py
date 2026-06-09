"""In-process fake Meta client for local dev and tests. No network, no creds."""

from __future__ import annotations

import uuid

from app.models.social_account import SocialProvider
from app.services.meta.base import ConnectedAccount, PublishResult


class MockMetaClient:
    def build_oauth_url(self, state: str) -> str:
        return f"https://mock.local/oauth?state={state}"

    async def exchange_code_for_accounts(self, code: str) -> list[ConnectedAccount]:
        # Deterministic fake page + linked IG account.
        page_id = f"mock_page_{code[:6] or '000000'}"
        ig_id = f"mock_ig_{code[:6] or '000000'}"
        return [
            ConnectedAccount(
                provider=SocialProvider.facebook_page,
                external_id=page_id,
                display_name="Mock Coffee (Page)",
                access_token=f"mock-page-token-{page_id}",
                scopes=["pages_manage_posts", "pages_read_engagement"],
            ),
            ConnectedAccount(
                provider=SocialProvider.instagram,
                external_id=ig_id,
                display_name="@mock_coffee",
                access_token=f"mock-page-token-{page_id}",
                scopes=["instagram_basic", "instagram_content_publish"],
                ig_user_id=ig_id,
            ),
        ]

    async def publish_post(
        self,
        *,
        provider: SocialProvider,
        external_id: str,
        access_token: str,
        body: str,
        media_urls: list[str],
        ig_user_id: str | None = None,
    ) -> PublishResult:
        post_id = f"mock_post_{uuid.uuid4().hex[:12]}"
        return PublishResult(
            external_post_id=post_id,
            permalink=f"https://mock.local/{external_id}/{post_id}",
        )
