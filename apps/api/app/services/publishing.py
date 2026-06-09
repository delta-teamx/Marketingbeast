"""Publishing pipeline: create/schedule content and publish it via Meta.

Idempotency rule: a ContentTarget with an `external_post_id` is never published
again — so retries and the due-poller can run safely without double-posting.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.models.content import (
    ContentItem,
    ContentStatus,
    ContentTarget,
    ContentType,
    TargetStatus,
)
from app.models.social_account import SocialAccount
from app.services.crypto import decrypt_secret
from app.services.meta import get_meta_client
from app.services.meta.base import MetaClient, MetaError

logger = get_logger(__name__)


async def create_content_item(
    session: AsyncSession,
    *,
    brand_id: uuid.UUID,
    body: str,
    content_type: ContentType = ContentType.post,
    media_urls: list[str] | None = None,
    target_account_ids: list[uuid.UUID],
    scheduled_time: datetime | None = None,
) -> ContentItem:
    status = ContentStatus.scheduled if scheduled_time else ContentStatus.draft
    item = ContentItem(
        brand_id=brand_id,
        body=body,
        content_type=content_type,
        media_urls=media_urls,
        scheduled_time=scheduled_time,
        status=status,
    )
    session.add(item)
    await session.flush()
    for account_id in target_account_ids:
        session.add(
            ContentTarget(content_item_id=item.id, social_account_id=account_id)
        )
    await session.commit()
    return await _load_item(session, item.id)


async def publish_content_item(
    session: AsyncSession,
    item_id: uuid.UUID,
    meta_client: MetaClient | None = None,
) -> ContentItem:
    """Publish all not-yet-published targets of an item. Safe to call repeatedly."""
    client = meta_client or get_meta_client()
    item = await _load_item(session, item_id)
    if item is None:
        raise ValueError(f"content item {item_id} not found")

    item.status = ContentStatus.publishing

    for target in item.targets:
        if target.external_post_id:  # already published — never repeat
            continue
        account = await session.get(SocialAccount, target.social_account_id)
        if account is None or not account.access_token_encrypted:
            target.status = TargetStatus.failed
            target.error = "social account not connected"
            continue
        try:
            result = await client.publish_post(
                provider=account.provider,
                external_id=account.external_id or "",
                access_token=decrypt_secret(account.access_token_encrypted),
                body=item.body,
                media_urls=item.media_urls or [],
                ig_user_id=account.ig_user_id,
            )
            target.external_post_id = result.external_post_id
            target.permalink = result.permalink
            target.status = TargetStatus.published
            target.error = None
        except MetaError as exc:
            target.status = TargetStatus.failed
            target.error = str(exc)
            logger.warning("publish failed for target %s: %s", target.id, exc)

    _finalize_status(item)
    await session.commit()
    return await _load_item(session, item_id)


async def publish_due_content(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    meta_client: MetaClient | None = None,
) -> list[uuid.UUID]:
    """Publish every scheduled item whose time has arrived. Returns their ids."""
    now = now or datetime.now(UTC)
    due = (
        await session.scalars(
            select(ContentItem.id)
            .where(
                ContentItem.status == ContentStatus.scheduled,
                ContentItem.scheduled_time <= now,
            )
            .with_for_update(skip_locked=True)
        )
    ).all()
    for item_id in due:
        await publish_content_item(session, item_id, meta_client)
    return list(due)


def _finalize_status(item: ContentItem) -> None:
    statuses = {t.status for t in item.targets}
    if statuses == {TargetStatus.published}:
        item.status = ContentStatus.published
        item.published_at = datetime.now(UTC)
    elif TargetStatus.published in statuses:
        # Partial success — record published time but flag the failures stay visible.
        item.status = ContentStatus.published
        item.published_at = datetime.now(UTC)
    else:
        item.status = ContentStatus.failed


async def _load_item(session: AsyncSession, item_id: uuid.UUID) -> ContentItem:
    return await session.scalar(
        select(ContentItem)
        .where(ContentItem.id == item_id)
        .options(selectinload(ContentItem.targets))
    )
