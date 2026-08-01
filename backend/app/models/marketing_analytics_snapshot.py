"""ORM mapping for public.marketing_analytics_snapshots.

Maps 1:1 onto
supabase/migrations/20260801100025_marketing_analytics_snapshots.sql. Each
row is one point-in-time analytics reading for a business, optionally
scoped to one connected social account — social_connection_id is nullable
(ON DELETE SET NULL, not CASCADE, so deleting a connection later doesn't
erase historical readings). No platform column: when social_connection_id
is set, the platform is reachable via that connection; a snapshot with no
connection represents an aggregate across all of a business's platforms.

Every metric column is nullable — different platforms/pulls report
different subsets of these metrics, and NULL ("not reported") is kept
distinct from 0 ("reported as zero").
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.social_media_connection import SocialMediaConnection


class MarketingAnalyticsSnapshot(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "marketing_analytics_snapshots"
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
    followers: Mapped[int | None] = mapped_column(Integer)
    reach: Mapped[int | None] = mapped_column(Integer)
    impressions: Mapped[int | None] = mapped_column(Integer)
    engagement: Mapped[int | None] = mapped_column(Integer)
    likes: Mapped[int | None] = mapped_column(Integer)
    comments: Mapped[int | None] = mapped_column(Integer)
    shares: Mapped[int | None] = mapped_column(Integer)
    saves: Mapped[int | None] = mapped_column(Integer)
    profile_visits: Mapped[int | None] = mapped_column(Integer)
    website_clicks: Mapped[int | None] = mapped_column(Integer)
    follower_growth: Mapped[int | None] = mapped_column(Integer)
    engagement_rate: Mapped[float | None] = mapped_column(Numeric(6, 3))
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="marketing_analytics_snapshots"
    )
    social_connection: Mapped["SocialMediaConnection | None"] = relationship(
        back_populates="marketing_analytics_snapshots"
    )


Index(
    "idx_marketing_analytics_snapshots_business_profile",
    MarketingAnalyticsSnapshot.business_profile_id,
)
Index(
    "idx_marketing_analytics_snapshots_social_connection",
    MarketingAnalyticsSnapshot.social_connection_id,
)
Index(
    "idx_marketing_analytics_snapshots_captured_at",
    MarketingAnalyticsSnapshot.captured_at,
)
Index(
    "idx_marketing_analytics_snapshots_business_profile_captured_at",
    MarketingAnalyticsSnapshot.business_profile_id,
    MarketingAnalyticsSnapshot.captured_at,
)
