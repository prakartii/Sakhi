"""ORM mapping for public.business_profiles — the hub of the schema.

Maps 1:1 onto the table created in
supabase/migrations/20260801100005_business_profiles.sql and later extended
(additively — no existing column touched) by
supabase/migrations/20260801100019_business_profiles_onboarding_fields.sql.
Those two migrations remain the authoritative source for column
definitions; this model mirrors them exactly, including indexes and
constraints, so `alembic revision --autogenerate` run against the real
database produces an empty (or near-empty) diff.

Relationship targets are referenced by string class name and imported only
under `TYPE_CHECKING`, so this module never imports the ~11 child model
modules at runtime — those modules import this one instead (business_profile
-> {voice_log, business_memory, ...}, never the reverse). That keeps the
whole package's import graph a one-way star with no cycles; SQLAlchemy
resolves the string names once every module in app.models has been imported
(see app/models/__init__.py) and mappers are first configured.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    BusinessRegistrationType,
    BusinessStage,
    BusinessStatus,
    pg_enum,
)
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.brand_asset import BrandAsset
    from app.models.business_memory import BusinessMemory
    from app.models.content_calendar_item import ContentCalendarItem
    from app.models.conversation_history import ConversationHistory
    from app.models.forecast_history import ForecastHistory
    from app.models.inventory import Inventory
    from app.models.language import Language
    from app.models.marketing_analytics_snapshot import MarketingAnalyticsSnapshot
    from app.models.marketing_content_analysis import MarketingContentAnalysis
    from app.models.mentor_match import MentorMatch
    from app.models.notification import Notification
    from app.models.opportunity_match import OpportunityMatch
    from app.models.scheduled_post import ScheduledPost
    from app.models.scheme_match import SchemeMatch
    from app.models.social_media_connection import SocialMediaConnection
    from app.models.supplier import Supplier
    from app.models.transaction import Transaction
    from app.models.user import User
    from app.models.voice_log import VoiceLog
    from app.models.website import Website


class BusinessProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "business_profiles"
    # Fetch server-generated/onupdate values (id, created_at, updated_at)
    # via RETURNING right after INSERT/UPDATE instead of a separate refresh.
    __mapper_args__ = {"eager_defaults": True}

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_category: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    registration_type: Mapped[BusinessRegistrationType] = mapped_column(
        pg_enum(BusinessRegistrationType, "business_registration_type_enum"),
        nullable=False,
        server_default=BusinessRegistrationType.UNREGISTERED.value,
    )
    gstin: Mapped[str | None] = mapped_column(String(15))
    pan: Mapped[str | None] = mapped_column(String(10))
    udyam_registration_number: Mapped[str | None] = mapped_column(String(30))
    year_established: Mapped[int | None] = mapped_column(SmallInteger)
    employee_count_range: Mapped[str | None] = mapped_column(String(20))
    monthly_revenue_range: Mapped[str | None] = mapped_column(String(30))
    preferred_language_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("languages.id", ondelete="SET NULL"),
    )
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default="India"
    )
    pincode: Mapped[str | None] = mapped_column(String(10))
    address: Mapped[str | None] = mapped_column(Text)
    logo_url: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    status: Mapped[BusinessStatus] = mapped_column(
        pg_enum(BusinessStatus, "business_status_enum"),
        nullable=False,
        server_default=BusinessStatus.ACTIVE.value,
    )

    # -- onboarding / growth-workflow fields --------------------------------
    # Added by supabase/migrations/20260801100019_business_profiles_onboarding_fields.sql.
    # All nullable: rows created before onboarding existed won't have these
    # set — see BusinessProfileService.get_onboarding_status, which reports
    # on exactly that gap rather than assuming it's filled in.
    owner_name: Mapped[str | None] = mapped_column(String(200))
    business_description: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(Text)
    products_or_services: Mapped[str | None] = mapped_column(Text)
    business_stage: Mapped[BusinessStage | None] = mapped_column(
        pg_enum(BusinessStage, "business_stage_enum")
    )
    website_url: Mapped[str | None] = mapped_column(Text)
    instagram_url: Mapped[str | None] = mapped_column(Text)
    facebook_url: Mapped[str | None] = mapped_column(Text)
    linkedin_url: Mapped[str | None] = mapped_column(Text)

    # -- relationships ----------------------------------------------------
    # ON DELETE behavior (CASCADE / SET NULL) is enforced by the database
    # via each child's FK, per the migrations — no ORM-level cascade= is
    # configured here, so SQLAlchemy never tries to duplicate that work.
    user: Mapped["User"] = relationship(back_populates="business_profiles")
    preferred_language: Mapped["Language | None"] = relationship(
        back_populates="business_profiles"
    )
    brand_assets: Mapped[list["BrandAsset"]] = relationship(
        back_populates="business_profile"
    )
    websites: Mapped[list["Website"]] = relationship(back_populates="business_profile")
    voice_logs: Mapped[list["VoiceLog"]] = relationship(
        back_populates="business_profile"
    )
    memories: Mapped[list["BusinessMemory"]] = relationship(
        back_populates="business_profile"
    )
    conversation_turns: Mapped[list["ConversationHistory"]] = relationship(
        back_populates="business_profile"
    )
    suppliers: Mapped[list["Supplier"]] = relationship(
        back_populates="business_profile"
    )
    inventory_items: Mapped[list["Inventory"]] = relationship(
        back_populates="business_profile"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="business_profile"
    )
    scheme_matches: Mapped[list["SchemeMatch"]] = relationship(
        back_populates="business_profile"
    )
    opportunity_matches: Mapped[list["OpportunityMatch"]] = relationship(
        back_populates="business_profile"
    )
    mentor_matches: Mapped[list["MentorMatch"]] = relationship(
        back_populates="business_profile"
    )
    forecasts: Mapped[list["ForecastHistory"]] = relationship(
        back_populates="business_profile"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="business_profile"
    )
    social_media_connections: Mapped[list["SocialMediaConnection"]] = relationship(
        back_populates="business_profile"
    )
    content_calendar_items: Mapped[list["ContentCalendarItem"]] = relationship(
        back_populates="business_profile"
    )
    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
        back_populates="business_profile"
    )
    marketing_analytics_snapshots: Mapped[list["MarketingAnalyticsSnapshot"]] = (
        relationship(back_populates="business_profile")
    )
    marketing_content_analyses: Mapped[list["MarketingContentAnalysis"]] = relationship(
        back_populates="business_profile"
    )


Index("idx_business_profiles_user_id", BusinessProfile.user_id)
Index("idx_business_profiles_status", BusinessProfile.status)
Index("idx_business_profiles_category", BusinessProfile.business_category)
Index("idx_business_profiles_geo", BusinessProfile.state, BusinessProfile.city)
Index(
    "uq_business_profiles_primary_per_user",
    BusinessProfile.user_id,
    unique=True,
    postgresql_where=(BusinessProfile.is_primary.is_(True)),
)
