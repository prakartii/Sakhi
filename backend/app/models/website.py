"""ORM mapping for public.websites.

Maps 1:1 onto supabase/migrations/20260801100021_websites.sql (the websites
half — see website_version.py for the other table it defines).
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import WebsiteStatus, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.website_version import WebsiteVersion


class Website(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "websites"
    __mapper_args__ = {"eager_defaults": True}

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    website_name: Mapped[str] = mapped_column(String(200), nullable=False)
    deployment_url: Mapped[str | None] = mapped_column(Text)
    github_repository: Mapped[str | None] = mapped_column(String(300))
    template: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[WebsiteStatus] = mapped_column(
        pg_enum(WebsiteStatus, "website_status_enum"),
        nullable=False,
        server_default=WebsiteStatus.DRAFT.value,
    )
    seo_title: Mapped[str | None] = mapped_column(String(200))
    seo_description: Mapped[str | None] = mapped_column(String(300))
    custom_domain: Mapped[str | None] = mapped_column(String(255))
    favicon: Mapped[str | None] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    # Chat-curation fields (migration 26) — see that migration's comments.
    content: Mapped[dict | None] = mapped_column(JSONB)
    images: Mapped[dict | None] = mapped_column(JSONB)
    preview_slug: Mapped[str | None] = mapped_column(String(80))

    # -- relationships ----------------------------------------------------
    # ON DELETE CASCADE is enforced by the database (the FK above), not by
    # ORM cascade= — consistent with every other child table in this schema.
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="websites"
    )
    versions: Mapped[list["WebsiteVersion"]] = relationship(back_populates="website")


Index("idx_websites_business_profile", Website.business_profile_id)
Index("idx_websites_status", Website.status)
Index(
    "idx_websites_published",
    Website.business_profile_id,
    postgresql_where=(Website.published.is_(True)),
)
Index(
    "uq_websites_custom_domain",
    Website.custom_domain,
    unique=True,
    postgresql_where=(Website.custom_domain.isnot(None)),
)
Index(
    "uq_websites_preview_slug",
    Website.preview_slug,
    unique=True,
    postgresql_where=(Website.preview_slug.isnot(None)),
)
