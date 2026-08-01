"""ORM mapping for public.mentor_matches.

Maps 1:1 onto supabase/migrations/20260801100015_mentors_and_matches.sql
(the mentor_matches half — see mentor_profile.py for the other table it
defines). Association object between business_profiles and mentor_profiles
— see scheme_match.py for why this isn't a `secondary=` many-to-many.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MentorMatchStatus, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.mentor_profile import MentorProfile


class MentorMatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mentor_matches"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint(
            "business_profile_id", "mentor_id", name="uq_mentor_matches_business_mentor"
        ),
        CheckConstraint(
            "match_score between 0 and 100", name="chk_mentor_matches_score"
        ),
        CheckConstraint(
            "feedback_rating is null or feedback_rating between 1 and 5",
            name="chk_mentor_matches_feedback_rating",
        ),
    )

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    mentor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mentor_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    match_reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[MentorMatchStatus] = mapped_column(
        pg_enum(MentorMatchStatus, "mentor_match_status_enum"),
        nullable=False,
        server_default=MentorMatchStatus.SUGGESTED.value,
    )
    requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session_scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    feedback_rating: Mapped[int | None] = mapped_column(SmallInteger)
    feedback_text: Mapped[str | None] = mapped_column(Text)

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="mentor_matches"
    )
    mentor: Mapped["MentorProfile"] = relationship(back_populates="matches")


Index(
    "idx_mentor_matches_business_profile",
    MentorMatch.business_profile_id,
    MentorMatch.match_score.desc(),
)
Index("idx_mentor_matches_mentor", MentorMatch.mentor_id)
Index("idx_mentor_matches_status", MentorMatch.status)
