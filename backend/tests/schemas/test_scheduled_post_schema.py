"""Unit tests for Scheduled Post Pydantic validation. No DB involved."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.scheduled_post import ScheduledPostCreate, UpdateStatusRequest

_FUTURE = datetime.now(timezone.utc) + timedelta(days=1)


def _payload(**overrides) -> dict:
    data = {
        "business_profile_id": uuid.uuid4(),
        "content_calendar_id": uuid.uuid4(),
        "social_connection_id": uuid.uuid4(),
        "scheduled_time": _FUTURE,
    }
    data.update(overrides)
    return data


def test_minimal_payload_is_accepted():
    scheduled_post = ScheduledPostCreate(**_payload())
    assert scheduled_post.scheduled_time == _FUTURE


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        ScheduledPostCreate(**_payload(not_a_real_field="x"))


@pytest.mark.parametrize(
    "field",
    [
        "business_profile_id",
        "content_calendar_id",
        "social_connection_id",
        "scheduled_time",
    ],
)
def test_missing_required_field_rejected(field):
    payload = _payload()
    del payload[field]
    with pytest.raises(ValidationError):
        ScheduledPostCreate(**payload)


def test_naive_scheduled_time_is_assumed_utc():
    naive = datetime(2027, 6, 1, 10, 0, 0)
    scheduled_post = ScheduledPostCreate(**_payload(scheduled_time=naive))

    assert scheduled_post.scheduled_time.tzinfo is not None
    assert scheduled_post.scheduled_time == naive.replace(tzinfo=timezone.utc)


def test_aware_scheduled_time_is_preserved():
    aware = datetime(
        2027, 6, 1, 10, 0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30))
    )
    scheduled_post = ScheduledPostCreate(**_payload(scheduled_time=aware))

    assert scheduled_post.scheduled_time == aware


def test_update_status_request_requires_publishing_status():
    with pytest.raises(ValidationError):
        UpdateStatusRequest()


def test_update_status_request_accepts_minimal_payload():
    request = UpdateStatusRequest(publishing_status="published")
    assert request.published_url is None
    assert request.provider_response is None
    assert request.error_log is None


def test_update_status_request_unknown_field_rejected():
    with pytest.raises(ValidationError):
        UpdateStatusRequest(publishing_status="failed", not_a_real_field="x")


def test_update_status_request_invalid_status_rejected():
    with pytest.raises(ValidationError):
        UpdateStatusRequest(publishing_status="uploading")


@pytest.mark.parametrize("field", ["published_url", "error_log"])
def test_update_status_request_blank_optional_text_normalizes_to_none(field):
    request = UpdateStatusRequest(publishing_status="failed", **{field: "   "})
    assert getattr(request, field) is None


def test_update_status_request_accepts_provider_response_dict():
    request = UpdateStatusRequest(
        publishing_status="published",
        provider_response={"id": "12345", "permalink": "https://instagram.com/p/xyz"},
    )
    assert request.provider_response == {
        "id": "12345",
        "permalink": "https://instagram.com/p/xyz",
    }
