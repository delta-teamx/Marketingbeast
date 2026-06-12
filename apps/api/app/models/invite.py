"""Org invitations (agency team management)."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk
from app.models.membership import OrgRole


class InviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    revoked = "revoked"


class OrgInvite(Base, TimestampMixin):
    __tablename__ = "org_invites"

    id: Mapped[uuid.UUID] = uuid_pk()
    org_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    role: Mapped[OrgRole] = mapped_column(
        SAEnum(OrgRole, name="org_role"), default=OrgRole.member, nullable=False
    )
    token: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[InviteStatus] = mapped_column(
        SAEnum(InviteStatus, name="invite_status"),
        default=InviteStatus.pending,
        nullable=False,
        index=True,
    )
