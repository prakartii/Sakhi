"""ORM mapping for public.scheduled_posts.

Maps 1:1 onto supabase/migrations/20260801100024_scheduled_posts.sql. Each
row is one publishing attempt: a ContentCalendarItem queued to go out
through a specific SocialMediaConnection at a given time.
content_calendar_id and social_connection_id are both required — unlike
ContentCalendarItem.social_connection_id (nullable, content can be planned
before a connection exists), a *scheduled* post has nothing to publish
through without one.

provider_response is a plain JSONB column, mapped the same way as
GovernmentScheme.documents_required elsewhere in this schema. Nothing in
this model (or its repository/service) calls a platform API — see
app.services.scheduled_post's module docstring for what populates these
columns instead.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PublishingStatus, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.content_calendar_item import ContentCalendarItem
    from app.models.social_media_connection import SocialMediaConnection


class ScheduledPost(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scheduled_posts"
    __mapper_args__ = {"eager_defaults": True}

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    content_calendar_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content_calendar_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    social_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("social_media_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    publishing_status: Mapped[PublishingStatus] = mapped_column(
        pg_enum(PublishingStatus, "publishing_status_enum"),
        nullable=False,
        server_default=PublishingStatus.QUEUED.value,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    published_url: Mapped[str | None] = mapped_column(Text)
    provider_response: Mapped[dict | None] = mapped_column(JSONB)
    error_log: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="scheduled_posts"
    )
    content_calendar_item: Mapped["ContentCalendarItem"] = relationship(
        back_populates="scheduled_posts"
    )
    social_connection: Mapped["SocialMediaConnection"] = relationship(
        back_populates="scheduled_posts"
    )


Index("idx_scheduled_posts_business_profile", ScheduledPost.business_profile_id)
Index("idx_scheduled_posts_content_calendar", ScheduledPost.content_calendar_id)
Index("idx_scheduled_posts_social_connection", ScheduledPost.social_connection_id)
Index("idx_scheduled_posts_status", ScheduledPost.publishing_status)
Index(
    "idx_scheduled_posts_business_profile_scheduled_time",
    ScheduledPost.business_profile_id,
    ScheduledPost.scheduled_time,
)
