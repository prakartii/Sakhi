"""Business logic for Marketing Analytics.

Owns the transaction boundary (commit/rollback) around Store Snapshot and
translates database-level failures into domain exceptions the API layer
maps to HTTP status codes — routers never see SQLAlchemy exceptions
directly. Whether social_connection_id actually belongs to the same
business requires reading another row's data, not just this payload's
shape, so it's checked here (store_snapshot only — see below for why the
read/aggregate methods don't repeat the check).

Get Daily/Weekly/Monthly Analytics, Compare Time Periods, and the Summary
Endpoint are all thin wrappers around
MarketingAnalyticsSnapshotRepository's SQL aggregates (sum/avg/count) —
this module does not compute anything a database aggregate function
couldn't. No AI, no forecasting, no platform API calls anywhere here.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import Row
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_analytics_snapshot import MarketingAnalyticsSnapshot
from app.repositories.marketing_analytics_snapshot import (
    MarketingAnalyticsSnapshotRepository,
)
from app.repositories.social_media_connection import SocialMediaConnectionRepository
from app.schemas.marketing_analytics_snapshot import (
    AnalyticsSummary,
    MarketingAnalyticsSnapshotCreate,
    MetricChange,
    PeriodAnalytics,
    PeriodComparison,
)

_BUCKET_DELTAS = {"day": timedelta(days=1), "week": timedelta(weeks=1)}
_DEFAULT_SUMMARY_WINDOW_DAYS = 30


class MarketingAnalyticsSnapshotNotFoundError(Exception):
    """No marketing_analytics_snapshots row exists for the given id."""


class InvalidReferenceError(Exception):
    """The referenced business_profile_id does not exist."""


class InvalidSocialConnectionError(Exception):
    """social_connection_id doesn't exist or doesn't belong to the same
    business."""


class InvalidSnapshotError(Exception):
    """captured_at is in the future."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "marketing_analytics_snapshots_business_profile_id_fkey" in message:
        return InvalidReferenceError(
            "business_profile_id does not reference an existing business profile."
        )
    if "marketing_analytics_snapshots_social_connection_id_fkey" in message:
        return InvalidSocialConnectionError(
            "social_connection_id does not reference an existing social "
            "media connection."
        )
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500.
    return exc


def _period_end_for_bucket(period_start: datetime, bucket: str) -> datetime:
    if bucket == "month":
        if period_start.month == 12:
            return period_start.replace(year=period_start.year + 1, month=1)
        return period_start.replace(month=period_start.month + 1)
    return period_start + _BUCKET_DELTAS[bucket]


def _row_to_period_analytics(
    row: Row, *, period_start: datetime, period_end: datetime
) -> PeriodAnalytics:
    return PeriodAnalytics(
        period_start=period_start,
        period_end=period_end,
        snapshot_count=row.snapshot_count,
        followers=float(row.followers) if row.followers is not None else None,
        reach=row.reach,
        impressions=row.impressions,
        engagement=row.engagement,
        likes=row.likes,
        comments=row.comments,
        shares=row.shares,
        saves=row.saves,
        profile_visits=row.profile_visits,
        website_clicks=row.website_clicks,
        follower_growth=row.follower_growth,
        engagement_rate=(
            float(row.engagement_rate) if row.engagement_rate is not None else None
        ),
    )


def _metric_change(a: float | int | None, b: float | int | None) -> MetricChange:
    change = None
    change_percent = None
    if a is not None and b is not None:
        change = b - a
        if a != 0:
            change_percent = (change / a) * 100
    return MetricChange(
        period_a=a, period_b=b, change=change, change_percent=change_percent
    )


class MarketingAnalyticsSnapshotService:
    def __init__(
        self,
        session: AsyncSession,
        repository: MarketingAnalyticsSnapshotRepository | None = None,
        connection_repository: SocialMediaConnectionRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or MarketingAnalyticsSnapshotRepository(session)
        self._connection_repo = (
            connection_repository or SocialMediaConnectionRepository(session)
        )

    async def _validate_social_connection(
        self, business_profile_id: uuid.UUID, social_connection_id: uuid.UUID | None
    ) -> None:
        if social_connection_id is None:
            return
        connection = await self._connection_repo.get_by_id(social_connection_id)
        if connection is None:
            raise InvalidSocialConnectionError(
                "social_connection_id does not reference an existing social "
                "media connection."
            )
        if connection.business_profile_id != business_profile_id:
            raise InvalidSocialConnectionError(
                "social_connection_id does not belong to the same "
                "business_profile_id."
            )

    async def store_snapshot(
        self, payload: MarketingAnalyticsSnapshotCreate
    ) -> MarketingAnalyticsSnapshot:
        if payload.captured_at > datetime.now(timezone.utc):
            raise InvalidSnapshotError("captured_at cannot be in the future.")
        await self._validate_social_connection(
            payload.business_profile_id, payload.social_connection_id
        )
        snapshot = MarketingAnalyticsSnapshot(**payload.model_dump())
        try:
            await self._repo.create(snapshot)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return snapshot

    async def get(self, snapshot_id: uuid.UUID) -> MarketingAnalyticsSnapshot:
        snapshot = await self._repo.get_by_id(snapshot_id)
        if snapshot is None:
            raise MarketingAnalyticsSnapshotNotFoundError(str(snapshot_id))
        return snapshot

    async def _bucketed(
        self,
        business_profile_id: uuid.UUID,
        *,
        bucket: str,
        start: datetime,
        end: datetime,
        social_connection_id: uuid.UUID | None,
    ) -> list[PeriodAnalytics]:
        rows = await self._repo.aggregate_by_bucket(
            business_profile_id,
            bucket=bucket,
            start=start,
            end=end,
            social_connection_id=social_connection_id,
        )
        return [
            _row_to_period_analytics(
                row,
                period_start=row.period_start,
                period_end=_period_end_for_bucket(row.period_start, bucket),
            )
            for row in rows
        ]

    async def get_daily_analytics(
        self,
        business_profile_id: uuid.UUID,
        *,
        start: datetime,
        end: datetime,
        social_connection_id: uuid.UUID | None = None,
    ) -> list[PeriodAnalytics]:
        return await self._bucketed(
            business_profile_id,
            bucket="day",
            start=start,
            end=end,
            social_connection_id=social_connection_id,
        )

    async def get_weekly_analytics(
        self,
        business_profile_id: uuid.UUID,
        *,
        start: datetime,
        end: datetime,
        social_connection_id: uuid.UUID | None = None,
    ) -> list[PeriodAnalytics]:
        return await self._bucketed(
            business_profile_id,
            bucket="week",
            start=start,
            end=end,
            social_connection_id=social_connection_id,
        )

    async def get_monthly_analytics(
        self,
        business_profile_id: uuid.UUID,
        *,
        start: datetime,
        end: datetime,
        social_connection_id: uuid.UUID | None = None,
    ) -> list[PeriodAnalytics]:
        return await self._bucketed(
            business_profile_id,
            bucket="month",
            start=start,
            end=end,
            social_connection_id=social_connection_id,
        )

    async def compare_periods(
        self,
        business_profile_id: uuid.UUID,
        *,
        period_a_start: datetime,
        period_a_end: datetime,
        period_b_start: datetime,
        period_b_end: datetime,
        social_connection_id: uuid.UUID | None = None,
    ) -> PeriodComparison:
        row_a = await self._repo.aggregate_period(
            business_profile_id,
            start=period_a_start,
            end=period_a_end,
            social_connection_id=social_connection_id,
        )
        row_b = await self._repo.aggregate_period(
            business_profile_id,
            start=period_b_start,
            end=period_b_end,
            social_connection_id=social_connection_id,
        )
        period_a = _row_to_period_analytics(
            row_a, period_start=period_a_start, period_end=period_a_end
        )
        period_b = _row_to_period_analytics(
            row_b, period_start=period_b_start, period_end=period_b_end
        )
        return PeriodComparison(
            period_a=period_a,
            period_b=period_b,
            followers=_metric_change(period_a.followers, period_b.followers),
            reach=_metric_change(period_a.reach, period_b.reach),
            impressions=_metric_change(period_a.impressions, period_b.impressions),
            engagement=_metric_change(period_a.engagement, period_b.engagement),
            likes=_metric_change(period_a.likes, period_b.likes),
            comments=_metric_change(period_a.comments, period_b.comments),
            shares=_metric_change(period_a.shares, period_b.shares),
            saves=_metric_change(period_a.saves, period_b.saves),
            profile_visits=_metric_change(
                period_a.profile_visits, period_b.profile_visits
            ),
            website_clicks=_metric_change(
                period_a.website_clicks, period_b.website_clicks
            ),
            follower_growth=_metric_change(
                period_a.follower_growth, period_b.follower_growth
            ),
            engagement_rate=_metric_change(
                period_a.engagement_rate, period_b.engagement_rate
            ),
        )

    async def summary(
        self,
        business_profile_id: uuid.UUID,
        *,
        days: int = _DEFAULT_SUMMARY_WINDOW_DAYS,
        social_connection_id: uuid.UUID | None = None,
    ) -> AnalyticsSummary:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        row = await self._repo.aggregate_period(
            business_profile_id,
            start=start,
            end=end,
            social_connection_id=social_connection_id,
        )
        period = _row_to_period_analytics(row, period_start=start, period_end=end)
        latest = await self._repo.get_latest(
            business_profile_id, social_connection_id=social_connection_id
        )
        return AnalyticsSummary(
            business_profile_id=business_profile_id,
            social_connection_id=social_connection_id,
            window_days=days,
            period=period,
            latest_snapshot=latest,
        )
