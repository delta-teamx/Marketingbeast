"""Unified inbox: sync comments/DMs, detect leads, draft replies.

Lead detection is a lightweight intent scorer (keyword heuristic in mock mode;
an LLM few-shot prompt in live mode). Replies are AI-DRAFTED and require user
confirmation — we never blast identical auto-replies (that trips spam systems).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.inbox import Conversation, ConversationStatus, ConversationType, Message
from app.models.social_account import SocialAccount
from app.services.crypto import decrypt_secret
from app.services.meta import get_meta_client
from app.services.meta.base import MetaClient

_INTENT_WEIGHTS = {
    "how much": 40, "price": 40, "cost": 35, "quote": 35,
    "buy": 40, "purchase": 40, "order": 35, "available": 30,
    "in stock": 30, "stock": 25, "book": 35, "appointment": 35,
    "reserve": 30, "interested": 25, "today": 12, "now": 8,
}
_LEAD_THRESHOLD = 40


def score_intent(text: str) -> int:
    low = text.lower()
    score = sum(w for kw, w in _INTENT_WEIGHTS.items() if kw in low)
    return min(score, 100)


async def sync_inbox(
    session: AsyncSession, brand_id: uuid.UUID, *, meta_client: MetaClient | None = None
) -> int:
    """Pull conversations for every connected account; upsert + score leads."""
    client = meta_client or get_meta_client()
    accounts = (
        await session.scalars(
            select(SocialAccount).where(
                SocialAccount.brand_id == brand_id,
                SocialAccount.status == "connected",
            )
        )
    ).all()

    count = 0
    for account in accounts:
        token = (
            decrypt_secret(account.access_token_encrypted)
            if account.access_token_encrypted
            else ""
        )
        convs = await client.fetch_conversations(
            provider=account.provider,
            external_id=account.external_id or "",
            access_token=token,
        )
        for cd in convs:
            conv = await session.scalar(
                select(Conversation)
                .where(
                    Conversation.social_account_id == account.id,
                    Conversation.external_id == cd.external_id,
                )
                .options(selectinload(Conversation.messages))
            )
            if conv is None:
                conv = Conversation(
                    brand_id=brand_id,
                    social_account_id=account.id,
                    external_id=cd.external_id,
                    conv_type=ConversationType(cd.conv_type),
                    participant_name=cd.participant_name,
                )
                session.add(conv)
                await session.flush()
                # New conversation — no existing messages. (Reading conv.messages
                # on a freshly-flushed persistent object would lazy-load → async
                # MissingGreenlet.) The found branch is eager-loaded below.
                known: set[str | None] = set()
            else:
                known = {m.external_id for m in conv.messages if m.external_id}
            best_score = conv.lead_score
            for md in cd.messages:
                sent_at = datetime.now(UTC) - timedelta(minutes=md.minutes_ago)
                if md.external_id not in known:
                    session.add(
                        Message(
                            conversation_id=conv.id,
                            external_id=md.external_id,
                            is_inbound=md.is_inbound,
                            text=md.text,
                            sent_at=sent_at,
                        )
                    )
                if md.is_inbound:
                    best_score = max(best_score, score_intent(md.text))
                conv.last_message_at = sent_at
            conv.lead_score = best_score
            conv.is_lead = best_score >= _LEAD_THRESHOLD
            count += 1
    await session.commit()
    return count


async def load_conversation(session: AsyncSession, conv_id: uuid.UUID) -> Conversation | None:
    return await session.scalar(
        select(Conversation)
        .where(Conversation.id == conv_id)
        .options(selectinload(Conversation.messages))
    )


async def draft_reply(session: AsyncSession, conv: Conversation) -> str:
    settings = get_settings()
    inbound = [m for m in sorted(conv.messages, key=lambda m: m.sent_at or datetime.now(UTC))
               if m.is_inbound]
    last = inbound[-1].text if inbound else ""
    name = conv.participant_name or "there"

    if settings.llm_provider != "mock":
        from app.services.llm import get_llm_provider
        from app.services.llm.base import Message as LLMMessage

        system = (
            "You are a friendly brand replying to a customer on social media. "
            "Write ONE short, helpful, non-generic reply. No hashtags."
        )
        result = get_llm_provider().generate(
            system, [LLMMessage(role="user", content=f"Customer said: {last}")]
        )
        return result.text.strip()

    if conv.is_lead:
        return (
            f"Hi {name}! Thanks for reaching out 🙌 Happy to help — I’ll send the "
            f"details and a quick way to grab it. What’s the best way to reach you?"
        )
    return f"Thanks so much, {name}! Really appreciate you 🙏"


async def post_reply(session: AsyncSession, conv: Conversation, text: str) -> Conversation:
    """Store the user-confirmed reply (live mode would also send via Graph API)."""
    session.add(
        Message(
            conversation_id=conv.id,
            is_inbound=False,
            text=text,
            sent_at=datetime.now(UTC),
        )
    )
    conv.status = ConversationStatus.replied
    conv.last_message_at = datetime.now(UTC)
    await session.commit()
    return await load_conversation(session, conv.id)


async def set_status(
    session: AsyncSession, conv: Conversation, status: ConversationStatus
) -> Conversation:
    conv.status = status
    await session.commit()
    return await load_conversation(session, conv.id)
