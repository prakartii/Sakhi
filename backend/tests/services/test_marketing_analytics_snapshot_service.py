"""Unit tests for MarketingAnalyticsSnapshotService. Both repositories and
the DB session are faked/mocked — no database connection is used or
required.

The fake repository below computes real sum/avg aggregates over an
in-memory store (rather than returning canned values), so these tests
exercise the service's bucketing/period-end/percent-change logic against
genuine aggregation, the same way the real Postgres-backed repository
would.
"""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.marketing_analytics_snapshot import MarketingAnalyticsSnapshot
from app.models.social_media_connection import SocialMediaConnection
from app.schemas.marketing_analytics_snapshot import MarketingAnalyticsSnapshotCreate
from app.services.marketing_analytics_snapshot import (
    InvalidReferenceError,
    InvalidSnapshotError,
    InvalidSocialConnectionError,
    MarketingAnalyticsSnapshotNotFoundError,
    MarketingAnalyticsSnapshotService,
)

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


def _truncate(value: datetime, bucket: str) -> datetime:
    start_of_day = value.replace(hour=0, minute=0, second=0, microsecond=0)
    if bucket == "day":
        return start_of_day
    if bucket == "week":
        return start_of_day - timedelta(days=start_of_day.weekday())
    if bucket == "month":
        return start_of_day.replace(day=1)
    raise ValueError(bucket)


class _FakeRepository:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, MarketingAnalyticsSnapshot] = {}
        self.raise_on_write: Exception | None = None

    async def create(
        self, snapshot: MarketingAnalyticsSnapshot
    ) -> MarketingAnalyticsSnapshot:
        if self.raise_on_write:
            raise self.raise_on_write
        # Real inserts populate these via eager_defaults' RETURNING; this
        # fake has to simulate that itself since nothing here ever touches
        # a database.
        now = datetime.now(timezone.utc)
        snapshot.id = snapshot.id or uuid.uuid4()
        snapshot.created_at = snapshot.created_at or now
        snapshot.updated_at = snapshot.updated_at or now
        self.store[snapshot.id] = snapshot
        return snapshot

    async def get_by_id(
        self, snapshot_id: uuid.UUID
    ) -> MarketingAnalyticsSnapshot | None:
        return self.store.get(snapshot_id)

    def _filtered(self, business_profile_id, start, end, social_connection_id):
        items = [
            s
            for s in self.store.values()
            if s.business_profile_id == business_profile_id
            and start <= s.captured_at < end
        ]
        if social_connection_id is not None:
            items = [s for s in items if s.social_connection_id == social_connection_id]
        return items

    def _aggregate(self, items) -> SimpleNamespace:
        def _sum(field):
            return sum((getattr(s, field) or 0) for s in items)

        def _avg(field):
            values = [getattr(s, field) for s in items if getattr(s, field) is not None]
            return (sum(values) / len(values)) if values else None

        data = {field: _sum(field) for field in _SUM_FIELDS}
        return SimpleNamespace(
            snapshot_count=len(items),
            followers=_avg("followers"),
            engagement_rate=_avg("engagement_rate"),
            **data,
        )

    async def aggregate_by_bucket(
        self, business_profile_id, *, bucket, start, end, social_connection_id=None
    ):
        items = self._filtered(business_profile_id, start, end, social_connection_id)
        buckets = defaultdict(list)
        for snapshot in items:
            buckets[_truncate(snapshot.captured_at, bucket)].append(snapshot)
        rows = []
        for period_start in sorted(buckets):
            agg = self._aggregate(buckets[period_start])
            rows.append(SimpleNamespace(period_start=period_start, **vars(agg)))
        return rows

    async def aggregate_period(
        self, business_profile_id, *, start, end, social_connection_id=None
    ):
        items = self._filtered(business_profile_id, start, end, social_connection_id)
        return self._aggregate(items)

    async def get_latest(self, business_profile_id, *, social_connection_id=None):
        items = [
            s
            for s in self.store.values()
            if s.business_profile_id == business_profile_id
        ]
        if social_connection_id is not None:
            items = [s for s in items if s.social_connection_id == social_connection_id]
        if not items:
            return None
        return max(items, key=lambda s: s.captured_at)


class _FakeConnectionRepository:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, SocialMediaConnection] = {}

    async def get_by_id(self, connection_id):
        return self.store.get(connection_id)


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _make_service():
    repo = _FakeRepository()
    connection_repo = _FakeConnectionRepository()
    session = AsyncMock()
    service = MarketingAnalyticsSnapshotService(
        session, repository=repo, connection_repository=connection_repo
    )
    return service, repo, connection_repo, session


def _payload(**overrides) -> MarketingAnalyticsSnapshotCreate:
    data = {
        "business_profile_id": uuid.uuid4(),
        "captured_at": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    data.update(overrides)
    return MarketingAnalyticsSnapshotCreate(**data)


async def test_store_snapshot_persists_and_commits():
    service, repo, _connection_repo, session = _make_service()

    result = await service.store_snapshot(_payload(followers=1000, reach=5000))

    assert result.id in repo.store
    assert result.followers == 1000
    session.commit.assert_awaited_once()


async def test_store_snapshot_rejects_future_captured_at():
    service, _repo, _connection_repo, _session = _make_service()
    future = datetime.now(timezone.utc) + timedelta(days=1)

    with pytest.raises(InvalidSnapshotError):
        await service.store_snapshot(_payload(captured_at=future))


async def test_store_snapshot_rejects_missing_social_connection():
    service, _repo, _connection_repo, _session = _make_service()

    with pytest.raises(InvalidSocialConnectionError):
        await service.store_snapshot(_payload(social_connection_id=uuid.uuid4()))


async def test_store_snapshot_rejects_social_connection_from_different_business():
    service, _repo, connection_repo, _session = _make_service()
    connection = SocialMediaConnection(
        id=uuid.uuid4(), business_profile_id=uuid.uuid4(), platform="instagram"
    )
    connection_repo.store[connection.id] = connection

    with pytest.raises(InvalidSocialConnectionError):
        await service.store_snapshot(
            _payload(
                business_profile_id=uuid.uuid4(), social_connection_id=connection.id
            )
        )


async def test_store_snapshot_accepts_valid_social_connection():
    service, _repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    connection = SocialMediaConnection(
        id=uuid.uuid4(), business_profile_id=business_profile_id, platform="instagram"
    )
    connection_repo.store[connection.id] = connection

    result = await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id, social_connection_id=connection.id
        )
    )

    assert result.social_connection_id == connection.id


async def test_store_snapshot_translates_invalid_business_profile_reference():
    service, repo, _connection_repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "marketing_analytics_snapshots" violates '
        "foreign key constraint "
        '"marketing_analytics_snapshots_business_profile_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.store_snapshot(_payload())


async def test_store_snapshot_reraises_unrecognized_integrity_error():
    service, repo, _connection_repo, _session = _make_service()
    repo.raise_on_write = _integrity_error("some_other_constraint_violation")

    with pytest.raises(IntegrityError):
        await service.store_snapshot(_payload())


async def test_get_missing_raises_not_found():
    service, _repo, _connection_repo, _session = _make_service()

    with pytest.raises(MarketingAnalyticsSnapshotNotFoundError):
        await service.get(uuid.uuid4())


async def test_get_existing_returns_snapshot():
    service, _repo, _connection_repo, _session = _make_service()
    created = await service.store_snapshot(_payload())

    fetched = await service.get(created.id)

    assert fetched is created


async def test_get_daily_analytics_buckets_by_day_and_sums_activity_metrics():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    day1 = datetime(2026, 3, 1, 9, tzinfo=timezone.utc)
    day1_later = datetime(2026, 3, 1, 18, tzinfo=timezone.utc)
    day2 = datetime(2026, 3, 2, 9, tzinfo=timezone.utc)
    await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id,
            captured_at=day1,
            likes=10,
            followers=100,
        )
    )
    await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id,
            captured_at=day1_later,
            likes=20,
            followers=110,
        )
    )
    await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id,
            captured_at=day2,
            likes=5,
            followers=115,
        )
    )

    buckets = await service.get_daily_analytics(
        business_profile_id,
        start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        end=datetime(2026, 3, 3, tzinfo=timezone.utc),
    )

    assert len(buckets) == 2
    assert buckets[0].period_start == datetime(2026, 3, 1, tzinfo=timezone.utc)
    assert buckets[0].period_end == datetime(2026, 3, 2, tzinfo=timezone.utc)
    assert buckets[0].snapshot_count == 2
    assert buckets[0].likes == 30  # summed
    assert buckets[0].followers == 105  # averaged
    assert buckets[1].likes == 5


async def test_get_weekly_analytics_buckets_by_week():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    # 2026-03-02 is a Monday.
    monday = datetime(2026, 3, 2, 9, tzinfo=timezone.utc)
    next_monday = datetime(2026, 3, 9, 9, tzinfo=timezone.utc)
    await service.store_snapshot(
        _payload(business_profile_id=business_profile_id, captured_at=monday, reach=100)
    )
    await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id, captured_at=next_monday, reach=200
        )
    )

    buckets = await service.get_weekly_analytics(
        business_profile_id,
        start=datetime(2026, 3, 1, tzinfo=timezone.utc),
        end=datetime(2026, 3, 15, tzinfo=timezone.utc),
    )

    assert len(buckets) == 2
    assert buckets[0].period_start == datetime(2026, 3, 2, tzinfo=timezone.utc)
    assert buckets[0].period_end == datetime(2026, 3, 9, tzinfo=timezone.utc)
    assert buckets[0].reach == 100


async def test_get_monthly_analytics_handles_december_rollover():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    december = datetime(2025, 12, 15, tzinfo=timezone.utc)
    await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id,
            captured_at=december,
            impressions=500,
        )
    )

    buckets = await service.get_monthly_analytics(
        business_profile_id,
        start=datetime(2025, 12, 1, tzinfo=timezone.utc),
        end=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert len(buckets) == 1
    assert buckets[0].period_start == datetime(2025, 12, 1, tzinfo=timezone.utc)
    assert buckets[0].period_end == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert buckets[0].impressions == 500


async def test_compare_periods_computes_change_and_percent():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id,
            captured_at=datetime(2026, 1, 15, tzinfo=timezone.utc),
            likes=100,
        )
    )
    await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id,
            captured_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
            likes=150,
        )
    )

    comparison = await service.compare_periods(
        business_profile_id,
        period_a_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        period_a_end=datetime(2026, 2, 1, tzinfo=timezone.utc),
        period_b_start=datetime(2026, 2, 1, tzinfo=timezone.utc),
        period_b_end=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )

    assert comparison.likes.period_a == 100
    assert comparison.likes.period_b == 150
    assert comparison.likes.change == 50
    assert comparison.likes.change_percent == 50.0


async def test_compare_periods_treats_zero_baseline_as_undefined_percent():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id,
            captured_at=datetime(2026, 2, 15, tzinfo=timezone.utc),
            likes=150,
        )
    )

    comparison = await service.compare_periods(
        business_profile_id,
        period_a_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        period_a_end=datetime(2026, 2, 1, tzinfo=timezone.utc),
        period_b_start=datetime(2026, 2, 1, tzinfo=timezone.utc),
        period_b_end=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )

    assert comparison.likes.period_a == 0
    assert comparison.likes.change == 150
    assert comparison.likes.change_percent is None


async def test_summary_returns_period_aggregate_and_latest_snapshot():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    older = await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id,
            captured_at=datetime.now(timezone.utc) - timedelta(days=5),
            followers=900,
        )
    )
    newer = await service.store_snapshot(
        _payload(
            business_profile_id=business_profile_id,
            captured_at=datetime.now(timezone.utc) - timedelta(hours=1),
            followers=1000,
        )
    )

    result = await service.summary(business_profile_id, days=30)

    assert result.window_days == 30
    assert result.latest_snapshot.id == newer.id
    assert result.latest_snapshot.id != older.id
    assert result.period.snapshot_count == 2


async def test_summary_with_no_snapshots_returns_none_latest():
    service, _repo, _connection_repo, _session = _make_service()

    result = await service.summary(uuid.uuid4())

    assert result.latest_snapshot is None
    assert result.period.snapshot_count == 0
    assert result.period.reach == 0
