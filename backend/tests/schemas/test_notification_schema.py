"""Unit tests for Notification Pydantic validation. No DB involved."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.notification import NotificationCreate, NotificationRead


def _payload(**overrides) -> dict:
    data = {
        "user_id": uuid.uuid4(),
        "notification_type": "system",
        "title": "Welcome to Sakhi",
    }
    data.update(overrides)
    return data


def test_minimal_payload_applies_defaults():
    notification = NotificationCreate(**_payload())

    assert notification.priority.value == "normal"
    assert notification.body is None
    assert notification.business_profile_id is None


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        NotificationCreate(**_payload(not_a_real_field="x"))


def test_missing_title_rejected():
    payload = _payload()
    del payload["title"]
    with pytest.raises(ValidationError):
        NotificationCreate(**payload)


def test_missing_notification_type_rejected():
    payload = _payload()
    del payload["notification_type"]
    with pytest.raises(ValidationError):
        NotificationCreate(**payload)


def test_missing_user_id_rejected():
    payload = _payload()
    del payload["user_id"]
    with pytest.raises(ValidationError):
        NotificationCreate(**payload)


def test_blank_title_rejected():
    with pytest.raises(ValidationError):
        NotificationCreate(**_payload(title="   "))


@pytest.mark.parametrize("field", ["body", "related_entity_type"])
def test_blank_optional_text_fields_normalize_to_none(field):
    notification = NotificationCreate(**_payload(**{field: "   "}))
    assert getattr(notification, field) is None


def test_valid_action_url_accepted():
    notification = NotificationCreate(
        **_payload(action_url="https://app.sakhi.example/inventory/low-stock")
    )
    assert notification.action_url == "https://app.sakhi.example/inventory/low-stock"


def test_invalid_action_url_rejected():
    with pytest.raises(ValidationError):
        NotificationCreate(**_payload(action_url="not-a-url"))


def test_invalid_notification_type_rejected():
    with pytest.raises(ValidationError):
        NotificationCreate(**_payload(notification_type="marketing_alert"))


def test_channel_is_not_settable_on_create():
    with pytest.raises(ValidationError):
        NotificationCreate(**_payload(channel="email"))


def test_read_schema_derives_unread_status_from_is_read_false():
    notification = NotificationRead(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        business_profile_id=None,
        notification_type="system",
        title="Welcome to Sakhi",
        body=None,
        action_url=None,
        related_entity_type=None,
        related_entity_id=None,
        channel="in_app",
        priority="normal",
        is_read=False,
        read_at=None,
        sent_at=None,
        created_at="2026-01-01T00:00:00Z",
    )

    assert notification.status == "unread"


def test_read_schema_derives_read_status_from_is_read_true():
    notification = NotificationRead(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        business_profile_id=None,
        notification_type="system",
        title="Welcome to Sakhi",
        body=None,
        action_url=None,
        related_entity_type=None,
        related_entity_id=None,
        channel="in_app",
        priority="normal",
        is_read=True,
        read_at="2026-01-02T00:00:00Z",
        sent_at=None,
        created_at="2026-01-01T00:00:00Z",
    )

    assert notification.status == "read"
