"""ORM mapping for public.opportunity_matches.

Maps 1:1 onto supabase/migrations/20260801100014_opportunities_and_matches.sql
(the opportunity_matches half — see opportunity.py for the other table it
defines). Association object between business_profiles and opportunities —
see scheme_match.py for why this isn't a `secondary=` many-to-many.
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
    from app.models.opportunity import Opportunity


class OpportunityMatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "opportunity_matches"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        UniqueConstraint(
            "business_profile_id",
            "opportunity_id",
            name="uq_opportunity_matches_business_opportunity",
        ),
        CheckConstraint(
            "match_score between 0 and 100", name="chk_opportunity_matches_score"
        ),
    )

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
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
        back_populates="opportunity_matches"
    )
    opportunity: Mapped["Opportunity"] = relationship(back_populates="matches")


Index(
    "idx_opportunity_matches_business_profile",
    OpportunityMatch.business_profile_id,
    OpportunityMatch.match_score.desc(),
)
Index("idx_opportunity_matches_opportunity", OpportunityMatch.opportunity_id)
Index("idx_opportunity_matches_status", OpportunityMatch.status)
