"""ORM mapping for public.website_versions.

Maps 1:1 onto supabase/migrations/20260801100021_websites.sql (the
website_versions half — see website.py for the other table it defines).

Append-only: rows are created by WebsiteService whenever a website is
created, updated, or archived, and never edited afterward.
version_number is assigned by the service (see
WebsiteService._next_version_number), not a DB sequence, because it's
scoped per-website rather than global — enforced here only by the
uq_website_versions_website_version unique constraint, which is what
actually prevents two concurrent writes from producing the same number.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import WebsiteStatus, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.website import Website


class WebsiteVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "website_versions"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint(
            "website_id", "version_number", name="uq_website_versions_website_version"
        ),
    )

    website_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("websites.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    website_name: Mapped[str] = mapped_column(String(200), nullable=False)
    deployment_url: Mapped[str | None] = mapped_column(Text)
    github_repository: Mapped[str | None] = mapped_column(String(300))
    template: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[WebsiteStatus] = mapped_column(
        pg_enum(WebsiteStatus, "website_status_enum"), nullable=False
    )
    seo_title: Mapped[str | None] = mapped_column(String(200))
    seo_description: Mapped[str | None] = mapped_column(String(300))
    custom_domain: Mapped[str | None] = mapped_column(String(255))
    favicon: Mapped[str | None] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False)
    change_notes: Mapped[str | None] = mapped_column(Text)

    # -- relationships ----------------------------------------------------
    website: Mapped["Website"] = relationship(back_populates="versions")


Index(
    "idx_website_versions_website",
    WebsiteVersion.website_id,
    WebsiteVersion.version_number.desc(),
)
