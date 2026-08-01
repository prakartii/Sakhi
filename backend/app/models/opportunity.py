"""ORM mapping for public.opportunities.

Maps 1:1 onto supabase/migrations/20260801100014_opportunities_and_matches.sql
(the opportunities half — see opportunity_match.py for the other table it
defines). A global catalog: no FKs of its own, matched to businesses via
opportunity_matches.
"""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import LocationScope, OpportunityType, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.opportunity_match import OpportunityMatch


class Opportunity(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "opportunities"
    __mapper_args__ = {"eager_defaults": True}

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    opportunity_type: Mapped[OpportunityType] = mapped_column(
        pg_enum(OpportunityType, "opportunity_type_enum"), nullable=False
    )
    source_name: Mapped[str | None] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text)
    eligibility_criteria: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    deadline: Mapped[date | None] = mapped_column(Date)
    location_scope: Mapped[LocationScope] = mapped_column(
        pg_enum(LocationScope, "location_scope_enum"),
        nullable=False,
        server_default=LocationScope.NATIONAL.value,
    )
    category: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    # -- relationships ----------------------------------------------------
    matches: Mapped[list["OpportunityMatch"]] = relationship(
        back_populates="opportunity"
    )


Index(
    "idx_opportunities_active",
    Opportunity.is_active,
    postgresql_where=(Opportunity.is_active.is_(True)),
)
Index("idx_opportunities_type", Opportunity.opportunity_type)
Index(
    "idx_opportunities_deadline",
    Opportunity.deadline,
    postgresql_where=(Opportunity.deadline.isnot(None)),
)
Index(
    "idx_opportunities_eligibility",
    Opportunity.eligibility_criteria,
    postgresql_using="gin",
)
