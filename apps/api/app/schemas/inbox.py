"""Unified inbox schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.inbox import ConversationStatus, ConversationType


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_inbound: bool
    text: str
    sent_at: datetime | None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brand_id: uuid.UUID
    conv_type: ConversationType
    participant_name: str | None
    status: ConversationStatus
    is_lead: bool
    lead_score: int
    last_message_at: datetime | None


class ConversationDetailOut(ConversationOut):
    messages: list[MessageOut]


class ReplyIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class DraftReplyOut(BaseModel):
    text: str
