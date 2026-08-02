"""ORM mapping for public.marketing_content_analyses.

Maps 1:1 onto
supabase/migrations/20260801100028_marketing_content_analyses.sql. See that
migration's docstring for why `analysis`/`reel_brief` are jsonb blobs
rather than one column per field, and why no raw image/video is stored.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MarketingAnalysisSourceType, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.social_media_connection import SocialMediaConnection


class MarketingContentAnalysis(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "marketing_content_analyses"
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
    source_type: Mapped[MarketingAnalysisSourceType] = mapped_column(
        pg_enum(MarketingAnalysisSourceType, "marketing_analysis_source_type_enum"),
        nullable=False,
        server_default=MarketingAnalysisSourceType.MANUAL.value,
    )
    source_url: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    hashtags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    comments_sample: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default=text("'{}'::text[]")
    )
    metrics: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    analysis: Mapped[dict | None] = mapped_column(JSONB)
    reel_brief: Mapped[dict | None] = mapped_column(JSONB)

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="marketing_content_analyses"
    )
    social_connection: Mapped["SocialMediaConnection | None"] = relationship(
        back_populates="marketing_content_analyses"
    )


Index(
    "idx_marketing_content_analyses_business_profile",
    MarketingContentAnalysis.business_profile_id,
    MarketingContentAnalysis.created_at.desc(),
)
Index(
    "idx_marketing_content_analyses_social_connection",
    MarketingContentAnalysis.social_connection_id,
)
