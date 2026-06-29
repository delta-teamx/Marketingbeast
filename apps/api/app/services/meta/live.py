"""Live Meta Graph API client (META_MODE=live).

Implements the official flows. Not exercised by the test suite (which uses the
mock); kept compliant and ready for real credentials + App Review.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urlsplit

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.social_account import SocialProvider
from app.services.meta.base import (
    ConnectedAccount,
    ConversationData,
    InsightsData,
    MessageData,
    MetaError,
    PublishResult,
)

logger = get_logger(__name__)

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


def _minutes_ago(created_time: str | None, now: datetime) -> int:
    """Minutes between a Graph ISO-8601 timestamp and now (0 if unparseable)."""
    if not created_time:
        return 0
    try:
        # Graph returns e.g. "2026-06-25T12:00:00+0000"; normalize the offset.
        ts = datetime.fromisoformat(created_time.replace("+0000", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        return max(0, int((now - ts).total_seconds() // 60))
    except ValueError:
        return 0


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

    @staticmethod
    def _day_window(day_offset: int) -> tuple[int, int]:
        """UTC [since, until) unix timestamps for the day `day_offset` days ago."""
        target = (datetime.now(UTC) - timedelta(days=day_offset)).date()
        since = int(datetime(target.year, target.month, target.day, tzinfo=UTC).timestamp())
        return since, since + 86_400

    @staticmethod
    def _latest_metric_values(payload: dict) -> dict[str, int]:
        """Flatten a Graph /insights response into {metric_name: latest int value}."""
        out: dict[str, int] = {}
        for metric in payload.get("data", []):
            name = metric.get("name")
            values = metric.get("values") or []
            if not name or not values:
                continue
            raw = values[-1].get("value", 0)
            # Some metrics return a dict breakdown; sum its numeric values.
            if isinstance(raw, dict):
                raw = sum(v for v in raw.values() if isinstance(v, (int, float)))
            try:
                out[name] = int(raw)
            except (TypeError, ValueError):
                out[name] = 0
        return out

    async def fetch_insights(
        self,
        *,
        provider: SocialProvider,
        external_id: str,
        access_token: str,
        day_offset: int = 0,
    ) -> InsightsData:
        """Pull one day of insights from the Graph API.

        The follower count is always read (the most basic call — a failure here
        means bad credentials, so we surface it). Day-bucketed reach/impressions/
        engagement and the post count are best-effort: if a metric is unavailable
        for this Graph version we record 0 for that field rather than failing the
        whole daily sync. (Exact metric availability is verified during Meta App
        Review with live credentials.)
        """
        since, until = self._day_window(day_offset)
        async with httpx.AsyncClient(timeout=30) as client:
            if provider == SocialProvider.facebook_page:
                profile = await client.get(
                    f"{self._base}/{external_id}",
                    params={"fields": "followers_count,fan_count", "access_token": access_token},
                )
                self._raise_for_error(profile)
                pj = profile.json()
                followers = int(pj.get("followers_count") or pj.get("fan_count") or 0)

                metrics = await self._safe_insights(
                    client,
                    f"{self._base}/{external_id}/insights",
                    {
                        "metric": "page_impressions,page_impressions_unique,page_post_engagements",
                        "period": "day",
                        "since": since,
                        "until": until,
                        "access_token": access_token,
                    },
                )
                posts = await self._safe_count(
                    client,
                    f"{self._base}/{external_id}/published_posts",
                    {"since": since, "until": until, "fields": "id", "limit": 100,
                     "access_token": access_token},
                )
                return InsightsData(
                    followers=followers,
                    reach=metrics.get("page_impressions_unique", 0),
                    impressions=metrics.get("page_impressions", 0),
                    engagement=metrics.get("page_post_engagements", 0),
                    posts=posts,
                )

            # Instagram business account.
            profile = await client.get(
                f"{self._base}/{external_id}",
                params={"fields": "followers_count", "access_token": access_token},
            )
            self._raise_for_error(profile)
            followers = int(profile.json().get("followers_count") or 0)

            metrics = await self._safe_insights(
                client,
                f"{self._base}/{external_id}/insights",
                {
                    "metric": "reach,impressions",
                    "period": "day",
                    "since": since,
                    "until": until,
                    "access_token": access_token,
                },
            )
            posts = await self._safe_count(
                client,
                f"{self._base}/{external_id}/media",
                {"since": since, "until": until, "fields": "id", "limit": 100,
                 "access_token": access_token},
            )
            reach = metrics.get("reach", 0)
            impressions = metrics.get("impressions", 0)
            return InsightsData(
                followers=followers,
                reach=reach,
                impressions=impressions,
                # IG account engagement isn't a stable single day metric across
                # versions; approximate with reach until App Review pins it down.
                engagement=0,
                posts=posts,
            )

    async def _safe_insights(
        self, client: httpx.AsyncClient, url: str, params: dict
    ) -> dict[str, int]:
        """GET an /insights edge, tolerating metric-availability errors (→ {})."""
        try:
            resp = await client.get(url, params=params)
            if resp.status_code >= 400:
                logger.warning("insights unavailable (%s): %s", resp.status_code, resp.text[:200])
                return {}
            return self._latest_metric_values(resp.json())
        except httpx.HTTPError as exc:
            logger.warning("insights request failed: %s", exc)
            return {}

    async def _safe_count(self, client: httpx.AsyncClient, url: str, params: dict) -> int:
        """GET a paged edge and count the returned items (best-effort → 0)."""
        try:
            resp = await client.get(url, params=params)
            if resp.status_code >= 400:
                return 0
            return len(resp.json().get("data", []))
        except httpx.HTTPError:
            return 0

    async def fetch_conversations(
        self,
        *,
        provider: SocialProvider,
        external_id: str,
        access_token: str,
    ) -> list[ConversationData]:
        """Pull recent Messenger/IG Direct conversations (the unified inbox).

        Uses the Graph `/conversations` edge. Requires pages_messaging /
        instagram_manage_messages (granted at App Review). On any Graph error we
        log and return [] so a single account's failure doesn't break the sync.
        """
        params = {
            "fields": "participants,messages.limit(10){message,from,created_time}",
            "limit": 25,
            "access_token": access_token,
        }
        if provider == SocialProvider.instagram:
            params["platform"] = "instagram"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{self._base}/{external_id}/conversations", params=params)
            if resp.status_code >= 400:
                logger.warning(
                    "conversations unavailable (%s): %s", resp.status_code, resp.text[:200]
                )
                return []
        except httpx.HTTPError as exc:
            logger.warning("conversations request failed: %s", exc)
            return []

        now = datetime.now(UTC)
        conversations: list[ConversationData] = []
        for thread in resp.json().get("data", []):
            participants = [p for p in thread.get("participants", {}).get("data", [])]
            # The other party is the participant whose id isn't this account.
            other = next(
                (p for p in participants if p.get("id") != external_id),
                participants[0] if participants else {},
            )
            messages: list[MessageData] = []
            for m in thread.get("messages", {}).get("data", []):
                messages.append(
                    MessageData(
                        external_id=m.get("id", ""),
                        text=m.get("message", ""),
                        is_inbound=(m.get("from", {}).get("id") != external_id),
                        minutes_ago=_minutes_ago(m.get("created_time"), now),
                    )
                )
            conversations.append(
                ConversationData(
                    external_id=thread.get("id", ""),
                    conv_type="dm",
                    participant_name=other.get("name", "Unknown"),
                    messages=list(reversed(messages)),  # oldest → newest
                )
            )
        return conversations

    @staticmethod
    def _raise_for_error(resp: httpx.Response) -> None:
        if resp.status_code >= 400:
            raise MetaError(f"Graph API {resp.status_code}: {resp.text}")
