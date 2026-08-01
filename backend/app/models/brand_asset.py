"""ORM mapping for public.brand_assets.

Maps 1:1 onto supabase/migrations/20260801100020_brand_assets.sql. A
business can have many brand_assets rows — successive rebrands, or a draft
being iterated on before it goes live — status distinguishes which one, if
any, is currently active. No uniqueness is enforced at the DB or model
level on "one active row per business"; that's a product decision left for
later, not assumed here.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import BrandAssetStatus, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile


class BrandAsset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "brand_assets"
    __mapper_args__ = {"eager_defaults": True}

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    brand_name: Mapped[str] = mapped_column(String(200), nullable=False)
    tagline: Mapped[str | None] = mapped_column(String(300))
    brand_story: Mapped[str | None] = mapped_column(Text)
    mission: Mapped[str | None] = mapped_column(Text)
    vision: Mapped[str | None] = mapped_column(Text)
    primary_color: Mapped[str | None] = mapped_column(String(7))
    secondary_color: Mapped[str | None] = mapped_column(String(7))
    typography: Mapped[str | None] = mapped_column(String(200))
    logo_url: Mapped[str | None] = mapped_column(Text)
    favicon_url: Mapped[str | None] = mapped_column(Text)
    brand_voice: Mapped[str | None] = mapped_column(Text)
    packaging_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[BrandAssetStatus] = mapped_column(
        pg_enum(BrandAssetStatus, "brand_asset_status_enum"),
        nullable=False,
        server_default=BrandAssetStatus.DRAFT.value,
    )

    # -- relationships ----------------------------------------------------
    # ON DELETE CASCADE is enforced by the database (the FK above), not by
    # ORM cascade= — consistent with every other child table in this schema.
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="brand_assets"
    )


Index("idx_brand_assets_business_profile", BrandAsset.business_profile_id)
Index("idx_brand_assets_status", BrandAsset.status)
Index(
    "idx_brand_assets_business_profile_status",
    BrandAsset.business_profile_id,
    BrandAsset.status,
)
