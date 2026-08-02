"""Python enums mirroring every Postgres enum type in the schema.

Values must match the Postgres enum labels exactly — see
supabase/migrations/20260801100002_enums.sql, the single source of truth
for these types. Centralized here (rather than one enum per model file) so
no model file needs to import another model file's module just to reuse an
enum, which keeps the dependency graph a strict star (every model ->
enums.py) instead of a mesh — the simplest way to avoid circular imports.
"""

from enum import Enum

from sqlalchemy import Enum as SAEnum


def pg_enum(enum_cls: type[Enum], name: str) -> SAEnum:
    """Builds a SQLAlchemy Enum type bound to an already-existing Postgres
    enum type. create_type=False (and, symmetrically, no drop) is load-bearing:
    these enum types are created by supabase/migrations/20260801100002_enums.sql,
    never by SQLAlchemy/Alembic DDL — without it, a stray create_all() or
    autogenerate could attempt `CREATE TYPE` against a type that already
    exists in Supabase and fail.
    """
    return SAEnum(
        enum_cls,
        name=name,
        create_type=False,
        values_callable=lambda cls: [member.value for member in cls],
    )


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class BusinessRegistrationType(str, Enum):
    UNREGISTERED = "unregistered"
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    PARTNERSHIP = "partnership"
    LLP = "llp"
    PRIVATE_LIMITED = "private_limited"
    PUBLIC_LIMITED = "public_limited"
    SECTION8 = "section8"
    COOPERATIVE = "cooperative"
    OTHER = "other"


class BusinessStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class BusinessStage(str, Enum):
    """Self-reported growth stage, set during onboarding. See
    supabase/migrations/20260801100019_business_profiles_onboarding_fields.sql."""

    IDEA = "idea"
    STARTUP = "startup"
    GROWING = "growing"
    SCALING = "scaling"


class BrandAssetStatus(str, Enum):
    """See supabase/migrations/20260801100020_brand_assets.sql."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class WebsiteStatus(str, Enum):
    """See supabase/migrations/20260801100021_websites.sql. Shared by
    websites and website_versions (a version snapshots the status the
    website had at that point)."""

    DRAFT = "draft"
    BUILDING = "building"
    LIVE = "live"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"


class VoiceLogStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    TRANSCRIBED = "transcribed"
    FAILED = "failed"


class MemoryType(str, Enum):
    FACT = "fact"
    MILESTONE = "milestone"
    GOAL = "goal"
    CHALLENGE = "challenge"
    PREFERENCE = "preference"
    NOTE = "note"
    DECISION = "decision"


class MemorySource(str, Enum):
    VOICE = "voice"
    MANUAL = "manual"
    AI_INFERRED = "ai_inferred"
    CONVERSATION = "conversation"
    IMPORT = "import"


class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    SYSTEM_EVENT = "system_event"


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"


class PaymentMethod(str, Enum):
    CASH = "cash"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    CHEQUE = "cheque"
    OTHER = "other"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class TransactionSource(str, Enum):
    MANUAL = "manual"
    VOICE = "voice"
    IMPORT = "import"
    POS = "pos"


class RecurringFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class InventoryMovementType(str, Enum):
    RESTOCK = "restock"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    WASTAGE = "wastage"
    RETURN = "return"


class SchemeLevel(str, Enum):
    CENTRAL = "central"
    STATE = "state"
    DISTRICT = "district"


class MatchStatus(str, Enum):
    """Shared by scheme_matches and opportunity_matches — both are
    "surfaced to a business, business reacts to it" workflows with an
    identical lifecycle."""

    SUGGESTED = "suggested"
    VIEWED = "viewed"
    SAVED = "saved"
    APPLIED = "applied"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OpportunityType(str, Enum):
    GRANT = "grant"
    TENDER = "tender"
    MARKETPLACE = "marketplace"
    COLLABORATION = "collaboration"
    LOAN = "loan"
    COMPETITION = "competition"
    TRAINING = "training"


class LocationScope(str, Enum):
    LOCAL = "local"
    STATE = "state"
    NATIONAL = "national"
    GLOBAL = "global"


class MentorAvailability(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"


class MentorMatchStatus(str, Enum):
    """Distinct from MatchStatus: mentor matching has a human-scheduling
    lifecycle (requested -> accepted -> completed), not an
    apply-to-a-listing lifecycle."""

    SUGGESTED = "suggested"
    VIEWED = "viewed"
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    DECLINED = "declined"


class NotificationType(str, Enum):
    SCHEME_MATCH = "scheme_match"
    OPPORTUNITY_MATCH = "opportunity_match"
    MENTOR_MATCH = "mentor_match"
    INVENTORY_ALERT = "inventory_alert"
    CASHFLOW_ALERT = "cashflow_alert"
    FORECAST_READY = "forecast_ready"
    SYSTEM = "system"
    REMINDER = "reminder"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WHATSAPP = "whatsapp"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ForecastType(str, Enum):
    CASHFLOW = "cashflow"
    REVENUE = "revenue"
    INVENTORY_DEMAND = "inventory_demand"
    GROWTH_SCORE = "growth_score"


class SocialMediaPlatform(str, Enum):
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    PINTEREST = "pinterest"


class MarketingAnalysisSourceType(str, Enum):
    MANUAL = "manual"
    SCREENSHOT = "screenshot"
    VIDEO_FRAME = "video_frame"
    LINK = "link"


class SocialConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"
    ERROR = "error"


class ContentType(str, Enum):
    POST = "post"
    STORY = "story"
    REEL = "reel"
    CAROUSEL = "carousel"
    VIDEO = "video"


class ContentStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PublishingStatus(str, Enum):
    QUEUED = "queued"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"
