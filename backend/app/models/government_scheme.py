"""ORM mapping for public.government_schemes.

Maps 1:1 onto supabase/migrations/20260801100013_schemes_and_matches.sql
(the government_schemes half — see scheme_match.py for the other table it
defines). A global catalog: no FKs of its own, matched to businesses via
scheme_matches.
"""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SchemeLevel, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.scheme_match import SchemeMatch


class GovernmentScheme(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "government_schemes"
    __mapper_args__ = {"eager_defaults": True}

    scheme_name: Mapped[str] = mapped_column(String(300), nullable=False)
    scheme_code: Mapped[str | None] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    issuing_authority: Mapped[str | None] = mapped_column(String(200))
    scheme_level: Mapped[SchemeLevel] = mapped_column(
        pg_enum(SchemeLevel, "scheme_level_enum"),
        nullable=False,
        server_default=SchemeLevel.CENTRAL.value,
    )
    applicable_states: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    eligibility_criteria: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    benefits: Mapped[str | None] = mapped_column(Text)
    application_url: Mapped[str | None] = mapped_column(Text)
    documents_required: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    category: Mapped[str | None] = mapped_column(String(100))
    min_business_age_months: Mapped[int | None] = mapped_column(Integer)
    max_annual_turnover: Mapped[float | None] = mapped_column(Numeric(16, 2))
    target_gender: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="women"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    valid_from: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)

    # -- relationships ----------------------------------------------------
    matches: Mapped[list["SchemeMatch"]] = relationship(back_populates="scheme")


Index(
    "idx_government_schemes_active",
    GovernmentScheme.is_active,
    postgresql_where=(GovernmentScheme.is_active.is_(True)),
)
Index("idx_government_schemes_category", GovernmentScheme.category)
Index("idx_government_schemes_level", GovernmentScheme.scheme_level)
Index(
    "idx_government_schemes_states",
    GovernmentScheme.applicable_states,
    postgresql_using="gin",
)
Index(
    "idx_government_schemes_eligibility",
    GovernmentScheme.eligibility_criteria,
    postgresql_using="gin",
)
