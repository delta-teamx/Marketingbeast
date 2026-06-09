"""Meta client interface + value objects shared by the mock and live adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.models.social_account import SocialProvider


@dataclass
class ConnectedAccount:
    """A page or IG account discovered during OAuth, ready to persist."""

    provider: SocialProvider
    external_id: str
    display_name: str
    access_token: str  # page token (FB) — encrypted before storage
    scopes: list[str] = field(default_factory=list)
    # For Instagram: the IG business account id (linked via the FB Page).
    ig_user_id: str | None = None


@dataclass
class PublishResult:
    external_post_id: str
    permalink: str | None = None


class MetaError(Exception):
    """Raised on any Graph API failure."""


@runtime_checkable
class MetaClient(Protocol):
    def build_oauth_url(self, state: str) -> str:
        """The Facebook Login dialog URL to send the user to."""
        ...

    async def exchange_code_for_accounts(self, code: str) -> list[ConnectedAccount]:
        """Exchange an OAuth code for tokens and list the user's pages + IG accounts."""
        ...

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
        """Publish a post/photo to a Page or IG account."""
        ...
