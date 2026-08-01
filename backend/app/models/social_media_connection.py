"""ORM mapping for public.social_media_connections.

Maps 1:1 onto
supabase/migrations/20260801100022_social_media_connections.sql. Distinct
from BusinessProfile.instagram_url/facebook_url/linkedin_url (plain profile
links, added by migration 19) — this table stores authenticated platform
connections: OAuth-style tokens and sync state from an actual connect flow.

access_token/refresh_token are mapped as plain Text columns; nothing here
encrypts or otherwise transforms them. That's deliberate — the migration's
column comment and app.services.social_media_connection's module docstring
both establish the service layer as the one place that reads/writes these
two columns, so adding encryption later is a service-layer change, not a
model or router change.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SocialConnectionStatus, SocialMediaPlatform, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.content_calendar_item import ContentCalendarItem
    from app.models.marketing_analytics_snapshot import MarketingAnalyticsSnapshot
    from app.models.scheduled_post import ScheduledPost


class SocialMediaConnection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "social_media_connections"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint(
            "business_profile_id",
            "platform",
            name="uq_social_media_connections_business_profile_platform",
        ),
    )

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    platform: Mapped[SocialMediaPlatform] = mapped_column(
        pg_enum(SocialMediaPlatform, "social_media_platform_enum"), nullable=False
    )
    account_name: Mapped[str | None] = mapped_column(String(200))
    account_id: Mapped[str | None] = mapped_column(String(200))
    profile_url: Mapped[str | None] = mapped_column(Text)
    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    connection_status: Mapped[SocialConnectionStatus] = mapped_column(
        pg_enum(SocialConnectionStatus, "social_connection_status_enum"),
        nullable=False,
        server_default=SocialConnectionStatus.CONNECTED.value,
    )
    last_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="social_media_connections"
    )
    content_calendar_items: Mapped[list["ContentCalendarItem"]] = relationship(
        back_populates="social_connection"
    )
    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
        back_populates="social_connection"
    )
    marketing_analytics_snapshots: Mapped[list["MarketingAnalyticsSnapshot"]] = (
        relationship(back_populates="social_connection")
    )


Index(
    "idx_social_media_connections_business_profile",
    SocialMediaConnection.business_profile_id,
)
Index(
    "idx_social_media_connections_status",
    SocialMediaConnection.connection_status,
)
