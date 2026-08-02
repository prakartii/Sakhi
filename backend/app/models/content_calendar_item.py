"""ORM mapping for public.content_calendar_items.

Maps 1:1 onto supabase/migrations/20260801100023_content_calendar_items.sql.
Each row is one planned piece of content for one business;
social_connection_id optionally ties it to an authenticated platform
connection (SocialMediaConnection) but is nullable — content can be planned
before an account is connected, and ON DELETE SET NULL (not CASCADE) means
disconnecting/removing a connection later doesn't take planned content with
it.

hashtags is a Postgres text[] column, mapped the same way as
GovernmentScheme.applicable_states / MentorProfile.expertise_areas
elsewhere in this schema.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ContentStatus, ContentType, SocialMediaPlatform, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.scheduled_post import ScheduledPost
    from app.models.social_media_connection import SocialMediaConnection


class ContentCalendarItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "content_calendar_items"
    __mapper_args__ = {"eager_defaults": True}

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    social_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_media_connections.id", ondelete="SET NULL"),
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_type: Mapped[ContentType] = mapped_column(
        pg_enum(ContentType, "content_type_enum"), nullable=False
    )
    platform: Mapped[SocialMediaPlatform] = mapped_column(
        pg_enum(SocialMediaPlatform, "social_media_platform_enum"), nullable=False
    )
    caption: Mapped[str | None] = mapped_column(Text)
    hashtags: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    image_prompt: Mapped[str | None] = mapped_column(Text)
    generated_image_url: Mapped[str | None] = mapped_column(Text)
    generated_video_url: Mapped[str | None] = mapped_column(Text)
    call_to_action: Mapped[str | None] = mapped_column(String(200))
    scheduled_datetime: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[ContentStatus] = mapped_column(
        pg_enum(ContentStatus, "content_status_enum"),
        nullable=False,
        server_default=ContentStatus.DRAFT.value,
    )
    ai_generated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="content_calendar_items"
    )
    social_connection: Mapped["SocialMediaConnection | None"] = relationship(
        back_populates="content_calendar_items"
    )
    scheduled_posts: Mapped[list["ScheduledPost"]] = relationship(
        back_populates="content_calendar_item"
    )


Index(
    "idx_content_calendar_items_business_profile",
    ContentCalendarItem.business_profile_id,
)
Index(
    "idx_content_calendar_items_social_connection",
    ContentCalendarItem.social_connection_id,
)
Index("idx_content_calendar_items_status", ContentCalendarItem.status)
Index("idx_content_calendar_items_platform", ContentCalendarItem.platform)
Index(
    "idx_content_calendar_items_business_profile_scheduled",
    ContentCalendarItem.business_profile_id,
    ContentCalendarItem.scheduled_datetime,
)
