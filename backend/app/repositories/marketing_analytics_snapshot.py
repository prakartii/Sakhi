"""Data-access layer for marketing_analytics_snapshots.

Builds on BaseRepository for create/get_by_id — no update/delete/list are
needed here: snapshots are insert-only facts (no "Update Snapshot" or
"Delete Snapshot" operation was asked for, and none would make sense for a
point-in-time reading). The three additions are the module's actual job:
simple SQL aggregation over stored rows.

  * aggregate_by_bucket — one aggregate row per day/week/month within a
    range (Postgres date_trunc as the GROUP BY key), backing Get Daily/
    Weekly/Monthly Analytics.
  * aggregate_period — one aggregate row over a single range, backing
    Compare Time Periods and the Summary Endpoint.
  * get_latest — the most recent snapshot row, backing the Summary
    Endpoint's "current followers" figure.

Aggregation choices, applied consistently in both methods:
  * followers — AVG. It's a gauge (a count of "current state"), not an
    activity total; summing it across snapshots would be meaningless.
    Documented here once rather than at every call site.
  * engagement_rate — AVG, for the same reason (a rate, not a count).
  * everything else (reach/impressions/engagement/likes/comments/shares/
    saves/profile_visits/website_clicks/follower_growth) — SUM, coalesced
    to 0 so a bucket with rows but no data for one metric reads as "0 this
    period," not None. followers/engagement_rate are left nullable (None
    means "no reading," not "zero followers").

No search() here — this table has no free-text fields; every column is a
number, a timestamp, or a foreign key, so a substring search wouldn't mean
anything. Not registered in the generic repository smoke-test loop for the
same reason ScheduledPostRepository isn't — see that repository's module
docstring.
"""

import uuid
from datetime import datetime

from sqlalchemy import Row, and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_analytics_snapshot import MarketingAnalyticsSnapshot
from app.repositories.base import BaseRepository, RepositoryError

_SUM_FIELDS = (
    "reach",
    "impressions",
    "engagement",
    "likes",
    "comments",
    "shares",
    "saves",
    "profile_visits",
    "website_clicks",
    "follower_growth",
)


class MarketingAnalyticsSnapshotRepository(BaseRepository[MarketingAnalyticsSnapshot]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MarketingAnalyticsSnapshot)

    def _aggregate_columns(self) -> list:
        columns = [
            func.count().label("snapshot_count"),
            func.avg(MarketingAnalyticsSnapshot.followers).label("followers"),
            func.avg(MarketingAnalyticsSnapshot.engagement_rate).label(
                "engagement_rate"
            ),
        ]
        for field in _SUM_FIELDS:
            column = getattr(MarketingAnalyticsSnapshot, field)
            columns.append(func.coalesce(func.sum(column), 0).label(field))
        return columns

    def _conditions(
        self,
        business_profile_id: uuid.UUID,
        *,
        start: datetime,
        end: datetime,
        social_connection_id: uuid.UUID | None,
    ) -> list:
        conditions = [
            MarketingAnalyticsSnapshot.business_profile_id == business_profile_id,
            MarketingAnalyticsSnapshot.captured_at >= start,
            MarketingAnalyticsSnapshot.captured_at < end,
        ]
        if social_connection_id is not None:
            conditions.append(
                MarketingAnalyticsSnapshot.social_connection_id == social_connection_id
            )
        return conditions

    async def aggregate_by_bucket(
        self,
        business_profile_id: uuid.UUID,
        *,
        bucket: str,
        start: datetime,
        end: datetime,
        social_connection_id: uuid.UUID | None = None,
    ) -> list[Row]:
        """One row per `bucket` ('day'/'week'/'month') that has at least
        one snapshot in [start, end) — empty buckets are simply absent, not
        zero-filled, so the caller knows which periods actually have data.
        """
        period_start = func.date_trunc(
            bucket, MarketingAnalyticsSnapshot.captured_at
        ).label("period_start")
        conditions = self._conditions(
            business_profile_id,
            start=start,
            end=end,
            social_connection_id=social_connection_id,
        )
        stmt = (
            select(period_start, *self._aggregate_columns())
            .where(and_(*conditions))
            .group_by(period_start)
            .order_by(period_start)
        )
        try:
            return list((await self.session.execute(stmt)).all())
        except SQLAlchemyError as exc:
            raise RepositoryError(
                f"Failed to aggregate marketing analytics by {bucket} for "
                f"business_profile_id={business_profile_id!r}"
            ) from exc

    async def aggregate_period(
        self,
        business_profile_id: uuid.UUID,
        *,
        start: datetime,
        end: datetime,
        social_connection_id: uuid.UUID | None = None,
    ) -> Row:
        """One aggregate row over the whole [start, end) range — no
        grouping. snapshot_count is 0 (and every metric None/0 per the
        coalesce rules above) when nothing falls in range."""
        conditions = self._conditions(
            business_profile_id,
            start=start,
            end=end,
            social_connection_id=social_connection_id,
        )
        stmt = select(*self._aggregate_columns()).where(and_(*conditions))
        try:
            return (await self.session.execute(stmt)).one()
        except SQLAlchemyError as exc:
            raise RepositoryError(
                "Failed to aggregate marketing analytics for "
                f"business_profile_id={business_profile_id!r}"
            ) from exc

    async def get_latest(
        self,
        business_profile_id: uuid.UUID,
        *,
        social_connection_id: uuid.UUID | None = None,
    ) -> MarketingAnalyticsSnapshot | None:
        conditions = [
            MarketingAnalyticsSnapshot.business_profile_id == business_profile_id
        ]
        if social_connection_id is not None:
            conditions.append(
                MarketingAnalyticsSnapshot.social_connection_id == social_connection_id
            )
        stmt = (
            select(MarketingAnalyticsSnapshot)
            .where(and_(*conditions))
            .order_by(MarketingAnalyticsSnapshot.captured_at.desc())
            .limit(1)
        )
        try:
            return (await self.session.execute(stmt)).scalars().first()
        except SQLAlchemyError as exc:
            raise RepositoryError(
                "Failed to fetch latest marketing analytics snapshot for "
                f"business_profile_id={business_profile_id!r}"
            ) from exc
