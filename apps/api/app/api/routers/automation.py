"""Tier B group-post QUEUE — storage only.

The backend stores tasks that the user's local browser extension will later
claim and post under the §9 pacing guardrails. This server NEVER posts into
Facebook groups and never holds Facebook credentials (see brief §2/§9).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_brand_access
from app.core.security import AuthenticatedUser
from app.models.group import GroupPostTask, GroupSuggestion, GroupTaskStatus
from app.schemas.group import GroupPostTaskOut, GroupQueueCreate, GroupTaskUpdate

router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.post("/group-queue", response_model=GroupPostTaskOut, status_code=201)
async def queue_group_post(
    payload: GroupQueueCreate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> GroupPostTask:
    await require_brand_access(payload.brand_id, session=session, user=user)
    suggestion = await session.get(GroupSuggestion, payload.group_suggestion_id)
    if suggestion is None or suggestion.brand_id != payload.brand_id:
        raise HTTPException(status_code=400, detail="Suggestion does not belong to brand")

    task = GroupPostTask(
        brand_id=payload.brand_id,
        group_suggestion_id=payload.group_suggestion_id,
        body=payload.body,
        media_urls=payload.media_urls,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.get("/group-queue", response_model=list[GroupPostTaskOut])
async def list_group_queue(
    brand_id: uuid.UUID,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> list[GroupPostTask]:
    await require_brand_access(brand_id, session=session, user=user)
    rows = (
        await session.scalars(
            select(GroupPostTask)
            .where(GroupPostTask.brand_id == brand_id)
            .order_by(GroupPostTask.created_at.desc())
        )
    ).all()
    return list(rows)


# Allowed status transitions reported by the Tier B extension as it works a task.
_ALLOWED_TRANSITIONS: dict[GroupTaskStatus, set[GroupTaskStatus]] = {
    GroupTaskStatus.queued: {GroupTaskStatus.claimed, GroupTaskStatus.skipped},
    GroupTaskStatus.claimed: {GroupTaskStatus.posted, GroupTaskStatus.skipped},
}


@router.patch("/group-queue/{task_id}", response_model=GroupPostTaskOut)
async def update_group_task(
    task_id: uuid.UUID,
    payload: GroupTaskUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> GroupPostTask:
    """The extension claims a task, then reports it posted/skipped after the user
    confirms the post in their own browser. The server only records state."""
    task = await session.get(GroupPostTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await require_brand_access(task.brand_id, session=session, user=user)

    allowed = _ALLOWED_TRANSITIONS.get(task.status, set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot move task from {task.status.value} to {payload.status.value}",
        )
    task.status = payload.status
    if payload.external_ref is not None:
        task.external_ref = payload.external_ref
    await session.commit()
    await session.refresh(task)
    return task
