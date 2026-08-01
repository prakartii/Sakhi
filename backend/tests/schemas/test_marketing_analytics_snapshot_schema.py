"""Unit tests for Marketing Analytics Pydantic validation. No DB involved."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.marketing_analytics_snapshot import MarketingAnalyticsSnapshotCreate

_NOW = datetime.now(timezone.utc)


def _payload(**overrides) -> dict:
    data = {
        "business_profile_id": uuid.uuid4(),
        "captured_at": _NOW - timedelta(hours=1),
    }
    data.update(overrides)
    return data


def test_minimal_payload_is_accepted():
    snapshot = MarketingAnalyticsSnapshotCreate(**_payload())

    assert snapshot.social_connection_id is None
    assert snapshot.followers is None
    assert snapshot.follower_growth is None


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        MarketingAnalyticsSnapshotCreate(**_payload(not_a_real_field="x"))


def test_missing_business_profile_id_rejected():
    payload = _payload()
    del payload["business_profile_id"]
    with pytest.raises(ValidationError):
        MarketingAnalyticsSnapshotCreate(**payload)


def test_missing_captured_at_rejected():
    payload = _payload()
    del payload["captured_at"]
    with pytest.raises(ValidationError):
        MarketingAnalyticsSnapshotCreate(**payload)


@pytest.mark.parametrize(
    "field",
    [
        "followers",
        "reach",
        "impressions",
        "engagement",
        "likes",
        "comments",
        "shares",
        "saves",
        "profile_visits",
        "website_clicks",
    ],
)
def test_negative_count_fields_rejected(field):
    with pytest.raises(ValidationError):
        MarketingAnalyticsSnapshotCreate(**_payload(**{field: -1}))


def test_full_payload_accepted():
    snapshot = MarketingAnalyticsSnapshotCreate(
        **_payload(
            social_connection_id=uuid.uuid4(),
            followers=1000,
            reach=5000,
            impressions=8000,
            engagement=400,
            likes=300,
            comments=50,
            shares=30,
            saves=20,
            profile_visits=120,
            website_clicks=15,
            follower_growth=25,
            engagement_rate=5.5,
        )
    )

    assert snapshot.followers == 1000
    assert snapshot.engagement_rate == 5.5


def test_follower_growth_allows_negative_values():
    snapshot = MarketingAnalyticsSnapshotCreate(**_payload(follower_growth=-12))
    assert snapshot.follower_growth == -12


def test_negative_engagement_rate_rejected():
    with pytest.raises(ValidationError):
        MarketingAnalyticsSnapshotCreate(**_payload(engagement_rate=-1.0))


def test_naive_captured_at_is_assumed_utc():
    naive = datetime(2026, 6, 1, 10, 0, 0)
    snapshot = MarketingAnalyticsSnapshotCreate(**_payload(captured_at=naive))

    assert snapshot.captured_at.tzinfo is not None
    assert snapshot.captured_at == naive.replace(tzinfo=timezone.utc)


def test_aware_captured_at_is_preserved():
    aware = datetime(
        2026, 6, 1, 10, 0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30))
    )
    snapshot = MarketingAnalyticsSnapshotCreate(**_payload(captured_at=aware))

    assert snapshot.captured_at == aware
