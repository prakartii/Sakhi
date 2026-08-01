"""ORM mapping for public.forecast_history.

Maps 1:1 onto supabase/migrations/20260801100016_forecast_and_notifications.sql
(the forecast_history half — see notification.py for the other table it
defines), plus the one cross-table index migration 17 adds against this
table.
"""

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ForecastType, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile


class ForecastHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "forecast_history"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        CheckConstraint(
            "confidence_score is null or confidence_score between 0 and 100",
            name="chk_forecast_history_confidence",
        ),
        CheckConstraint(
            "forecast_period_end >= forecast_period_start",
            name="chk_forecast_history_period",
        ),
    )

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    forecast_type: Mapped[ForecastType] = mapped_column(
        pg_enum(ForecastType, "forecast_type_enum"), nullable=False
    )
    forecast_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    forecast_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_values: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    actual_values: Mapped[dict | None] = mapped_column(JSONB)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    model_version: Mapped[str | None] = mapped_column(String(50))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="forecasts"
    )


Index(
    "idx_forecast_history_business_profile",
    ForecastHistory.business_profile_id,
    ForecastHistory.forecast_period_start.desc(),
)
Index("idx_forecast_history_type", ForecastHistory.forecast_type)
# From supabase/migrations/20260801100017_performance_indexes.sql.
Index(
    "idx_forecast_history_profile_type_generated",
    ForecastHistory.business_profile_id,
    ForecastHistory.forecast_type,
    ForecastHistory.generated_at.desc(),
)
