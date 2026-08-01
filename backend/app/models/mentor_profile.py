"""ORM mapping for public.mentor_profiles.

Maps 1:1 onto supabase/migrations/20260801100015_mentors_and_matches.sql
(the mentor_profiles half — see mentor_match.py for the other table it
defines).
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MentorAvailability, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.mentor_match import MentorMatch
    from app.models.user import User


class MentorProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mentor_profiles"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        CheckConstraint(
            "rating is null or rating between 0 and 5",
            name="chk_mentor_profiles_rating",
        ),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    expertise_areas: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, server_default=text("'{}'::text[]")
    )
    industry_focus: Mapped[str | None] = mapped_column(String(100))
    years_experience: Mapped[int | None] = mapped_column(Integer)
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2))
    total_sessions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    availability_status: Mapped[MentorAvailability] = mapped_column(
        pg_enum(MentorAvailability, "mentor_availability_enum"),
        nullable=False,
        server_default=MentorAvailability.AVAILABLE.value,
    )
    hourly_rate: Mapped[float | None] = mapped_column(Numeric(10, 2))

    # -- relationships ----------------------------------------------------
    user: Mapped["User | None"] = relationship(back_populates="mentor_profiles")
    matches: Mapped[list["MentorMatch"]] = relationship(back_populates="mentor")


Index("idx_mentor_profiles_user", MentorProfile.user_id)
Index(
    "idx_mentor_profiles_active",
    MentorProfile.is_active,
    postgresql_where=(MentorProfile.is_active.is_(True)),
)
Index("idx_mentor_profiles_availability", MentorProfile.availability_status)
Index(
    "idx_mentor_profiles_expertise",
    MentorProfile.expertise_areas,
    postgresql_using="gin",
)
