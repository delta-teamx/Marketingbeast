"""Unified inbox: sync, list, conversation detail, AI-draft reply, send, moderate."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.security import AuthenticatedUser
from app.models.inbox import Conversation, ConversationStatus
from app.schemas.inbox import (
    ConversationDetailOut,
    ConversationOut,
    DraftReplyOut,
    ReplyIn,
)
from app.services.inbox import (
    draft_reply,
    load_conversation,
    post_reply,
    set_status,
    sync_inbox,
)

router = APIRouter(prefix="/api", tags=["inbox"])


async def _conv_for_user(
    session: AsyncSession, conv_id: uuid.UUID, user: AuthenticatedUser
) -> Conversation:
    conv = await load_conversation(session, conv_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await require_brand_access(conv.brand_id, session=session, user=user)
    return conv


@router.post("/brands/{brand_id}/inbox/sync", response_model=list[ConversationOut])
async def sync_brand_inbox(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[Conversation]:
    await require_brand_access(brand_id, session=session, user=user)
    await sync_inbox(session, brand_id)
    return await _list(session, brand_id)


@router.get("/brands/{brand_id}/inbox", response_model=list[ConversationOut])
async def list_inbox(
    brand_id: uuid.UUID,
    leads_only: bool = False,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[Conversation]:
    await require_brand_access(brand_id, session=session, user=user)
    return await _list(session, brand_id, leads_only=leads_only)


async def _list(
    session: AsyncSession, brand_id: uuid.UUID, *, leads_only: bool = False
) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .where(Conversation.brand_id == brand_id)
        .order_by(Conversation.is_lead.desc(), Conversation.last_message_at.desc())
    )
    if leads_only:
        stmt = stmt.where(Conversation.is_lead.is_(True))
    return list((await session.scalars(stmt)).all())


@router.get("/conversations/{conv_id}", response_model=ConversationDetailOut)
async def conversation_detail(
    conv_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Conversation:
    return await _conv_for_user(session, conv_id, user)


@router.post("/conversations/{conv_id}/draft-reply", response_model=DraftReplyOut)
async def conversation_draft_reply(
    conv_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> DraftReplyOut:
    conv = await _conv_for_user(session, conv_id, user)
    return DraftReplyOut(text=await draft_reply(session, conv))


@router.post("/conversations/{conv_id}/reply", response_model=ConversationDetailOut)
async def conversation_reply(
    conv_id: uuid.UUID,
    payload: ReplyIn,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Conversation:
    conv = await _conv_for_user(session, conv_id, user)
    return await post_reply(session, conv, payload.text)


@router.post("/conversations/{conv_id}/hide", response_model=ConversationDetailOut)
async def conversation_hide(
    conv_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Conversation:
    conv = await _conv_for_user(session, conv_id, user)
    return await set_status(session, conv, ConversationStatus.hidden)
