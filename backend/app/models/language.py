"""ORM mapping for public.languages.

Maps 1:1 onto supabase/migrations/20260801100003_languages.sql. Pure lookup
table — no FKs of its own, referenced (optionally) by users, business_profiles
and voice_logs.
"""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.user import User
    from app.models.voice_log import VoiceLog


class Language(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "languages"
    __mapper_args__ = {"eager_defaults": True}

    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    native_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    # -- relationships ----------------------------------------------------
    users: Mapped[list["User"]] = relationship(back_populates="preferred_language")
    business_profiles: Mapped[list["BusinessProfile"]] = relationship(
        back_populates="preferred_language"
    )
    voice_logs: Mapped[list["VoiceLog"]] = relationship(back_populates="language")


Index(
    "idx_languages_active",
    Language.is_active,
    postgresql_where=(Language.is_active.is_(True)),
)
