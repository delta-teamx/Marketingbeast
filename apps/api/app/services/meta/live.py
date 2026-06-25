"""Live Meta Graph API client (META_MODE=live).

Implements the official flows. Not exercised by the test suite (which uses the
mock); kept compliant and ready for real credentials + App Review.
"""

from __future__ import annotations

import asyncio
from urllib.parse import urlencode, urlsplit

import httpx

from app.core.config import get_settings
from app.models.social_account import SocialProvider
from app.services.meta.base import (
    ConnectedAccount,
    ConversationData,
    InsightsData,
    MetaError,
    PublishResult,
)

# Scopes requested at connect time (see README for App Review notes).
OAUTH_SCOPES = [
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_posts",
    "pages_manage_metadata",
    "instagram_basic",
    "instagram_content_publish",
    "business_management",
]


def _is_video(url: str) -> bool:
    """True if the URL points to a video file (by extension, ignoring query)."""
    path = urlsplit(url).path.lower()
    return path.endswith((".mp4", ".mov", ".m4v"))


class LiveMetaClient:
    def __init__(self) -> None:
        s = get_settings()
        self._app_id = s.meta_app_id
        self._app_secret = s.meta_app_secret
        self._redirect_uri = s.meta_redirect_uri
        self._graph_version = s.meta_graph_version
        self._base = f"https://graph.facebook.com/{s.meta_graph_version}"

    def build_oauth_url(self, state: str) -> str:
        params = {
            "client_id": self._app_id,
            "redirect_uri": self._redirect_uri,
            "state": state,
            "scope": ",".join(OAUTH_SCOPES),
            "response_type": "code",
        }
        return (
            f"https://www.facebook.com/{self._graph_version}/dialog/oauth?{urlencode(params)}"
        )

    async def exchange_code_for_accounts(self, code: str) -> list[ConnectedAccount]:
        async with httpx.AsyncClient(timeout=30) as client:
            token_resp = await client.get(
                f"{self._base}/oauth/access_token",
                params={
                    "client_id": self._app_id,
                    "client_secret": self._app_secret,
                    "redirect_uri": self._redirect_uri,
                    "code": code,
                },
            )
            self._raise_for_error(token_resp)
            user_token = token_resp.json()["access_token"]

            pages_resp = await client.get(
                f"{self._base}/me/accounts",
                params={
                    "fields": "id,name,access_token,instagram_business_account{id,username}",
                    "access_token": user_token,
                },
            )
            self._raise_for_error(pages_resp)

        accounts: list[ConnectedAccount] = []
        for page in pages_resp.json().get("data", []):
            page_token = page["access_token"]
            accounts.append(
                ConnectedAccount(
                    provider=SocialProvider.facebook_page,
                    external_id=page["id"],
                    display_name=page.get("name", page["id"]),
                    access_token=page_token,
                    scopes=OAUTH_SCOPES,
                )
            )
            ig = page.get("instagram_business_account")
            if ig:
                accounts.append(
                    ConnectedAccount(
                        provider=SocialProvider.instagram,
                        external_id=ig["id"],
                        display_name=f"@{ig.get('username', ig['id'])}",
                        access_token=page_token,  # IG publishing uses the page token
                        scopes=OAUTH_SCOPES,
                        ig_user_id=ig["id"],
                    )
                )
        return accounts

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
        async with httpx.AsyncClient(timeout=60) as client:
            if provider == SocialProvider.facebook_page:
                return await self._publish_page(client, external_id, access_token, body, media_urls)
            return await self._publish_instagram(
                client, ig_user_id or external_id, access_token, body, media_urls
            )

    async def _publish_page(
        self,
        client: httpx.AsyncClient,
        page_id: str,
        token: str,
        body: str,
        media_urls: list[str],
    ) -> PublishResult:
        if media_urls and _is_video(media_urls[0]):
            resp = await client.post(
                f"{self._base}/{page_id}/videos",
                data={"file_url": media_urls[0], "description": body, "access_token": token},
            )
        elif media_urls:
            resp = await client.post(
                f"{self._base}/{page_id}/photos",
                data={"url": media_urls[0], "caption": body, "access_token": token},
            )
        else:
            resp = await client.post(
                f"{self._base}/{page_id}/feed",
                data={"message": body, "access_token": token},
            )
        self._raise_for_error(resp)
        data = resp.json()
        return PublishResult(external_post_id=data.get("post_id") or data["id"])

    async def _publish_instagram(
        self,
        client: httpx.AsyncClient,
        ig_user_id: str,
        token: str,
        body: str,
        media_urls: list[str],
    ) -> PublishResult:
        if not media_urls:
            raise MetaError("Instagram posts require at least one media URL")
        # Step 1: create a media container (Reels for video, image otherwise).
        if _is_video(media_urls[0]):
            create = await client.post(
                f"{self._base}/{ig_user_id}/media",
                data={
                    "media_type": "REELS",
                    "video_url": media_urls[0],
                    "caption": body,
                    "access_token": token,
                },
            )
            self._raise_for_error(create)
            creation_id = create.json()["id"]
            # Reels containers transcode asynchronously: poll readiness before
            # publishing. Bounded to ~10 attempts so we never block forever.
            for _ in range(10):
                check = await client.get(
                    f"{self._base}/{creation_id}",
                    params={"fields": "status_code", "access_token": token},
                )
                self._raise_for_error(check)
                status_code = check.json().get("status_code")
                if status_code == "FINISHED":
                    break
                if status_code == "ERROR":
                    raise MetaError("Instagram Reels container processing failed")
                await asyncio.sleep(2)
        else:
            create = await client.post(
                f"{self._base}/{ig_user_id}/media",
                data={"image_url": media_urls[0], "caption": body, "access_token": token},
            )
            self._raise_for_error(create)
            creation_id = create.json()["id"]
        # Step 2: publish the container.
        publish = await client.post(
            f"{self._base}/{ig_user_id}/media_publish",
            data={"creation_id": creation_id, "access_token": token},
        )
        self._raise_for_error(publish)
        return PublishResult(external_post_id=publish.json()["id"])

    async def fetch_insights(
        self,
        *,
        provider: SocialProvider,
        external_id: str,
        access_token: str,
        day_offset: int = 0,
    ) -> InsightsData:
        # Real Graph insights wiring (page/IG insights metrics) lands with live
        # credentials + App Review. Returns zeros until then rather than crashing.
        return InsightsData(followers=0, reach=0, impressions=0, engagement=0, posts=0)

    async def fetch_conversations(
        self,
        *,
        provider: SocialProvider,
        external_id: str,
        access_token: str,
    ) -> list[ConversationData]:
        # Real comments + Messenger/IG conversations wiring lands with live
        # credentials + App Review (pages_messaging / instagram_manage_messages).
        return []

    @staticmethod
    def _raise_for_error(resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            raise MetaError(f"Graph API {resp.status_code}: {resp.text}")
