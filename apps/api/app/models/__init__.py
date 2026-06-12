"""ORM models. Import all here so Alembic autogenerate sees them."""

from app.models.analytics import Competitor, MetricSnapshot, Report, ReportPeriod
from app.models.audit import AuditReport
from app.models.brand import Brand
from app.models.content import (
    ContentItem,
    ContentStatus,
    ContentTarget,
    ContentType,
    TargetStatus,
)
from app.models.group import (
    GroupPostTask,
    GroupSuggestion,
    GroupTaskStatus,
    SuggestionStatus,
)
from app.models.inbox import (
    Conversation,
    ConversationStatus,
    ConversationType,
    Message,
)
from app.models.membership import Membership, OrgRole
from app.models.onboarding import OnboardingProfile
from app.models.organization import Organization
from app.models.social_account import SocialAccount, SocialProvider

__all__ = [
    "AuditReport",
    "Brand",
    "Competitor",
    "Conversation",
    "ConversationStatus",
    "ConversationType",
    "Message",
    "MetricSnapshot",
    "Report",
    "ReportPeriod",
    "ContentItem",
    "ContentStatus",
    "ContentTarget",
    "ContentType",
    "GroupPostTask",
    "GroupSuggestion",
    "GroupTaskStatus",
    "Membership",
    "OnboardingProfile",
    "OrgRole",
    "Organization",
    "SocialAccount",
    "SocialProvider",
    "SuggestionStatus",
    "TargetStatus",
]
