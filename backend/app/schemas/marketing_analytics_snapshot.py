"""Pydantic v2 request/response schemas for Marketing Analytics.

Kept separate from app.models.marketing_analytics_snapshot (the ORM shape)
on purpose, same as every other module in this codebase. Two schema
families:

  * MarketingAnalyticsSnapshotCreate/Read — the raw stored fact, one row
    per "Store Snapshot" call.
  * PeriodAnalytics/PeriodComparison/AnalyticsSummary — the aggregate
    views app.services.marketing_analytics computes over stored rows for
    Get Daily/Weekly/Monthly Analytics, Compare Time Periods, and the
    Summary Endpoint. These never come from the database as one row; the
    service assembles them from repository aggregate queries.
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MarketingAnalyticsSnapshotCreate(BaseModel):
    """Payload for "Store Snapshot". Every metric is optional — different
    platforms/pulls report different subsets — except captured_at, which
    is what every aggregate view below groups and filters on."""

    model_config = ConfigDict(extra="forbid")

    business_profile_id: UUID = Field(
        description="The business this reading belongs to."
    )
    social_connection_id: UUID | None = Field(
        default=None,
        description="The connected account this reading is scoped to. "
        "Omit for a reading that aggregates across all of a business's "
        "connected platforms.",
    )
    followers: Annotated[int, Field(ge=0)] | None = None
    reach: Annotated[int, Field(ge=0)] | None = None
    impressions: Annotated[int, Field(ge=0)] | None = None
    engagement: Annotated[int, Field(ge=0)] | None = None
    likes: Annotated[int, Field(ge=0)] | None = None
    comments: Annotated[int, Field(ge=0)] | None = None
    shares: Annotated[int, Field(ge=0)] | None = None
    saves: Annotated[int, Field(ge=0)] | None = None
    profile_visits: Annotated[int, Field(ge=0)] | None = None
    website_clicks: Annotated[int, Field(ge=0)] | None = None
    # Not ge=0: a business can lose followers, and this is a delta, not a
    # count — unlike every other metric here.
    follower_growth: int | None = None
    engagement_rate: Annotated[float, Field(ge=0)] | None = None
    captured_at: datetime = Field(
        description="When this reading was captured on the platform side. "
        "Must not be in the future."
    )

    @field_validator("captured_at")
    @classmethod
    def _assume_utc_when_naive(cls, value: datetime) -> datetime:
        """A caller that sends an offset-less timestamp almost certainly
        means UTC (the column is timestamptz) rather than the server's
        local time — attaching UTC here keeps the "not in the future"
        check in the service from comparing naive vs. aware datetimes."""
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


class MarketingAnalyticsSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_profile_id: UUID
    social_connection_id: UUID | None
    followers: int | None
    reach: int | None
    impressions: int | None
    engagement: int | None
    likes: int | None
    comments: int | None
    shares: int | None
    saves: int | None
    profile_visits: int | None
    website_clicks: int | None
    follower_growth: int | None
    engagement_rate: float | None
    captured_at: datetime
    created_at: datetime
    updated_at: datetime


class PeriodAnalytics(BaseModel):
    """One aggregate bucket. followers/engagement_rate are averages
    (gauges/rates, not activity totals) and are None when the bucket has
    no snapshots; every other metric is a coalesced sum (0, not None, when
    the bucket has rows but no data for that particular metric)."""

    period_start: datetime
    period_end: datetime
    snapshot_count: int
    followers: float | None
    reach: int
    impressions: int
    engagement: int
    likes: int
    comments: int
    shares: int
    saves: int
    profile_visits: int
    website_clicks: int
    follower_growth: int
    engagement_rate: float | None


class PeriodAnalyticsListResponse(BaseModel):
    items: list[PeriodAnalytics]


class MetricChange(BaseModel):
    period_a: float | None
    period_b: float | None
    change: float | None = Field(description="period_b minus period_a.")
    change_percent: float | None = Field(
        description="Percent change from period_a to period_b. None when "
        "period_a is zero or None — percent change from nothing is "
        "undefined, not infinite."
    )


class PeriodComparison(BaseModel):
    period_a: PeriodAnalytics
    period_b: PeriodAnalytics
    followers: MetricChange
    reach: MetricChange
    impressions: MetricChange
    engagement: MetricChange
    likes: MetricChange
    comments: MetricChange
    shares: MetricChange
    saves: MetricChange
    profile_visits: MetricChange
    website_clicks: MetricChange
    follower_growth: MetricChange
    engagement_rate: MetricChange


class AnalyticsSummary(BaseModel):
    business_profile_id: UUID
    social_connection_id: UUID | None
    window_days: int
    period: PeriodAnalytics
    latest_snapshot: MarketingAnalyticsSnapshotRead | None = Field(
        description="The most recently captured snapshot, regardless of "
        "whether it falls inside `period` — None if no snapshot exists yet."
    )
