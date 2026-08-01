"""Endpoint-level tests for the Marketing Analytics API.

MarketingAnalyticsSnapshotService is replaced via FastAPI's
dependency_overrides with an in-memory fake, so these tests exercise
routing, status codes and response shapes without a live database.
Aggregation correctness (bucketing, sum/avg choices, percent-change math)
is already covered by tests/services/test_marketing_analytics_snapshot_service.py
against a repository fake that computes real aggregates — this file's fake
service keeps aggregation intentionally simple and just verifies the HTTP
contract: paths, status codes, validation, and response shape.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import pytest

from app.api.v1.endpoints import marketing_analytics_snapshots as endpoint_module
from app.main import app
from app.models.marketing_analytics_snapshot import MarketingAnalyticsSnapshot
from app.schemas.marketing_analytics_snapshot import (
    AnalyticsSummary,
    MetricChange,
    PeriodAnalytics,
    PeriodComparison,
)
from app.services.marketing_analytics_snapshot import (
    InvalidReferenceError,
    InvalidSnapshotError,
    InvalidSocialConnectionError,
    MarketingAnalyticsSnapshotNotFoundError,
)

BASE_URL = "/api/v1/marketing-analytics"
_PAST_ISO = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


def _zero_period(period_start, period_end, snapshot_count=0) -> PeriodAnalytics:
    return PeriodAnalytics(
        period_start=period_start,
        period_end=period_end,
        snapshot_count=snapshot_count,
        followers=None,
        reach=0,
        impressions=0,
        engagement=0,
        likes=0,
        comments=0,
        shares=0,
        saves=0,
        profile_visits=0,
        website_clicks=0,
        follower_growth=0,
        engagement_rate=None,
    )


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, MarketingAnalyticsSnapshot] = {}
        self.raise_on_store: Exception | None = None

    async def store_snapshot(self, payload):
        if self.raise_on_store:
            raise self.raise_on_store
        now = datetime.now(timezone.utc)
        snapshot = MarketingAnalyticsSnapshot(
            id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump()
        )
        self.store[snapshot.id] = snapshot
        return snapshot

    async def get(self, snapshot_id):
        snapshot = self.store.get(snapshot_id)
        if snapshot is None:
            raise MarketingAnalyticsSnapshotNotFoundError(str(snapshot_id))
        return snapshot

    async def get_daily_analytics(
        self, business_profile_id, *, start, end, social_connection_id=None
    ):
        return [_zero_period(start, start + timedelta(days=1), snapshot_count=1)]

    async def get_weekly_analytics(
        self, business_profile_id, *, start, end, social_connection_id=None
    ):
        return [_zero_period(start, start + timedelta(weeks=1), snapshot_count=1)]

    async def get_monthly_analytics(
        self, business_profile_id, *, start, end, social_connection_id=None
    ):
        return [_zero_period(start, end, snapshot_count=1)]

    async def compare_periods(
        self,
        business_profile_id,
        *,
        period_a_start,
        period_a_end,
        period_b_start,
        period_b_end,
        social_connection_id=None,
    ):
        no_change = MetricChange(period_a=0, period_b=0, change=0, change_percent=None)
        return PeriodComparison(
            period_a=_zero_period(period_a_start, period_a_end),
            period_b=_zero_period(period_b_start, period_b_end),
            followers=no_change,
            reach=no_change,
            impressions=no_change,
            engagement=no_change,
            likes=no_change,
            comments=no_change,
            shares=no_change,
            saves=no_change,
            profile_visits=no_change,
            website_clicks=no_change,
            follower_growth=no_change,
            engagement_rate=no_change,
        )

    async def summary(self, business_profile_id, *, days=30, social_connection_id=None):
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        latest = max(self.store.values(), key=lambda s: s.captured_at, default=None)
        return AnalyticsSummary(
            business_profile_id=business_profile_id,
            social_connection_id=social_connection_id,
            window_days=days,
            period=_zero_period(start, end, snapshot_count=len(self.store)),
            latest_snapshot=latest,
        )


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


def _store_payload(**overrides) -> dict:
    data = {
        "business_profile_id": str(uuid.uuid4()),
        "captured_at": _PAST_ISO,
        "followers": 1000,
        "likes": 50,
    }
    data.update(overrides)
    return data


async def test_store_snapshot_returns_201_with_created_snapshot(client, fake_service):
    response = await client.post(BASE_URL, json=_store_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["followers"] == 1000
    assert "id" in body and "created_at" in body


async def test_store_snapshot_missing_required_field_returns_422(client, fake_service):
    payload = _store_payload()
    del payload["captured_at"]

    response = await client.post(BASE_URL, json=payload)

    assert response.status_code == 422


async def test_store_snapshot_negative_metric_returns_422(client, fake_service):
    response = await client.post(BASE_URL, json=_store_payload(likes=-5))

    assert response.status_code == 422


async def test_store_snapshot_invalid_reference_returns_422(client, fake_service):
    fake_service.raise_on_store = InvalidReferenceError(
        "business_profile_id does not reference an existing business profile."
    )

    response = await client.post(BASE_URL, json=_store_payload())

    assert response.status_code == 422


async def test_store_snapshot_invalid_social_connection_returns_422(
    client, fake_service
):
    fake_service.raise_on_store = InvalidSocialConnectionError(
        "social_connection_id does not belong to the same business_profile_id."
    )

    response = await client.post(BASE_URL, json=_store_payload())

    assert response.status_code == 422


async def test_store_snapshot_future_captured_at_returns_422(client, fake_service):
    fake_service.raise_on_store = InvalidSnapshotError(
        "captured_at cannot be in the future."
    )

    response = await client.post(BASE_URL, json=_store_payload())

    assert response.status_code == 422


async def test_get_missing_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_existing_returns_200(client, fake_service):
    create_resp = await client.post(BASE_URL, json=_store_payload())
    snapshot_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{snapshot_id}")

    assert response.status_code == 200
    assert response.json()["id"] == snapshot_id


async def test_daily_analytics_requires_business_profile_id_start_end(
    client, fake_service
):
    response = await client.get(f"{BASE_URL}/daily")

    assert response.status_code == 422


async def test_daily_analytics_returns_bucketed_items(client, fake_service):
    response = await client.get(
        f"{BASE_URL}/daily",
        params={
            "business_profile_id": str(uuid.uuid4()),
            "start": "2026-03-01T00:00:00Z",
            "end": "2026-03-08T00:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["snapshot_count"] == 1


async def test_weekly_analytics_returns_bucketed_items(client, fake_service):
    response = await client.get(
        f"{BASE_URL}/weekly",
        params={
            "business_profile_id": str(uuid.uuid4()),
            "start": "2026-03-01T00:00:00Z",
            "end": "2026-03-31T00:00:00Z",
        },
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


async def test_monthly_analytics_returns_bucketed_items(client, fake_service):
    response = await client.get(
        f"{BASE_URL}/monthly",
        params={
            "business_profile_id": str(uuid.uuid4()),
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-04-01T00:00:00Z",
        },
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


async def test_compare_periods_returns_metric_changes(client, fake_service):
    response = await client.get(
        f"{BASE_URL}/compare",
        params={
            "business_profile_id": str(uuid.uuid4()),
            "period_a_start": "2026-01-01T00:00:00Z",
            "period_a_end": "2026-02-01T00:00:00Z",
            "period_b_start": "2026-02-01T00:00:00Z",
            "period_b_end": "2026-03-01T00:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "likes" in body
    assert body["likes"]["change_percent"] is None


async def test_compare_periods_missing_required_query_param_returns_422(
    client, fake_service
):
    response = await client.get(
        f"{BASE_URL}/compare", params={"business_profile_id": str(uuid.uuid4())}
    )

    assert response.status_code == 422


async def test_summary_returns_default_30_day_window(client, fake_service):
    await client.post(BASE_URL, json=_store_payload())

    response = await client.get(
        f"{BASE_URL}/summary", params={"business_profile_id": str(uuid.uuid4())}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["window_days"] == 30
    assert body["latest_snapshot"] is not None


async def test_summary_accepts_custom_days_window(client, fake_service):
    response = await client.get(
        f"{BASE_URL}/summary",
        params={"business_profile_id": str(uuid.uuid4()), "days": 7},
    )

    assert response.status_code == 200
    assert response.json()["window_days"] == 7


async def test_summary_invalid_days_returns_422(client, fake_service):
    response = await client.get(
        f"{BASE_URL}/summary",
        params={"business_profile_id": str(uuid.uuid4()), "days": 0},
    )

    assert response.status_code == 422


async def test_openapi_schema_documents_marketing_analytics_routes(
    client, fake_service
):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/daily" in paths
    assert f"{BASE_URL}/weekly" in paths
    assert f"{BASE_URL}/monthly" in paths
    assert f"{BASE_URL}/compare" in paths
    assert f"{BASE_URL}/summary" in paths
    assert f"{BASE_URL}/{{snapshot_id}}" in paths
