"""ORM mapping for public.scheme_matches.

Maps 1:1 onto supabase/migrations/20260801100013_schemes_and_matches.sql
(the scheme_matches half — see government_scheme.py for the other table it
defines).

This is the many-to-many between business_profiles and government_schemes,
modeled as an "association object" (a real entity with its own PK and
payload columns — match_score, status, ...) rather than a plain `secondary=`
join table. SQLAlchemy's own guidance is to use this pattern whenever the
association carries data beyond the two foreign keys, which is the case for
every *_matches table in this schema, so none of them get a bare
many-to-many relationship; they get two one-to-many relationships instead
(BusinessProfile.scheme_matches, GovernmentScheme.matches), which is what's
declared below.
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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MatchStatus, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.government_scheme import GovernmentScheme


class SchemeMatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "scheme_matches"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint(
            "business_profile_id", "scheme_id", name="uq_scheme_matches_business_scheme"
        ),
        CheckConstraint(
            "match_score between 0 and 100", name="chk_scheme_matches_score"
        ),
    )

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("government_schemes.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    match_reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[MatchStatus] = mapped_column(
        pg_enum(MatchStatus, "match_status_enum"),
        nullable=False,
        server_default=MatchStatus.SUGGESTED.value,
    )
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="scheme_matches"
    )
    scheme: Mapped["GovernmentScheme"] = relationship(back_populates="matches")


Index(
    "idx_scheme_matches_business_profile",
    SchemeMatch.business_profile_id,
    SchemeMatch.match_score.desc(),
)
Index("idx_scheme_matches_scheme", SchemeMatch.scheme_id)
Index("idx_scheme_matches_status", SchemeMatch.status)
