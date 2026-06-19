"""In-process fake Meta client for local dev and tests. No network, no creds."""

from __future__ import annotations

import uuid

from app.models.social_account import SocialProvider
from app.services.meta.base import (
    ConnectedAccount,
    ConversationData,
    InsightsData,
    MessageData,
    PublishResult,
)


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

    async def fetch_insights(
        self,
        *,
        provider: SocialProvider,
        external_id: str,
        access_token: str,
        day_offset: int = 0,
    ) -> InsightsData:
        # Deterministic from the account id; followers trend gently upward so the
        # most recent day (offset 0) is highest — charts show growth.
        seed = sum(ord(c) for c in external_id)
        base_followers = 800 + seed % 1200
        followers = base_followers + (30 - day_offset) * (5 + seed % 7)
        reach = 200 + (seed + day_offset * 13) % 900
        impressions = reach + 150 + (seed % 400)
        engagement = 20 + (seed + day_offset * 7) % 180
        posts = (seed + day_offset) % 3
        return InsightsData(
            followers=followers,
            reach=reach,
            impressions=impressions,
            engagement=engagement,
            posts=posts,
        )

    async def fetch_conversations(
        self,
        *,
        provider: SocialProvider,
        external_id: str,
        access_token: str,
    ) -> list[ConversationData]:
        # A deterministic mix of comments + DMs, including some buyer-intent leads.
        pre = external_id[-4:] or "0000"
        return [
            ConversationData(
                external_id=f"{pre}-c1",
                conv_type="comment",
                participant_name="Jordan P.",
                messages=[
                    MessageData(f"{pre}-c1-m1", "Love this! How much is it?", True, 35),
                ],
            ),
            ConversationData(
                external_id=f"{pre}-d1",
                conv_type="dm",
                participant_name="Sam R.",
                messages=[
                    MessageData(f"{pre}-d1-m1", "Hi! Do you have this in stock?", True, 90),
                    MessageData(f"{pre}-d1-m2", "I'd like to buy 2 today", True, 80),
                ],
            ),
            ConversationData(
                external_id=f"{pre}-c2",
                conv_type="comment",
                participant_name="Alex T.",
                messages=[
                    MessageData(f"{pre}-c2-m1", "Nice photo 🔥", True, 200),
                ],
            ),
        ]
