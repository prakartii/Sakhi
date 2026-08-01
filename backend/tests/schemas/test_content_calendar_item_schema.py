"""Unit tests for Content Calendar Pydantic validation. No DB involved."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.content_calendar_item import (
    ContentCalendarItemCreate,
    ContentCalendarItemUpdate,
)


def _payload(**overrides) -> dict:
    data = {
        "business_profile_id": uuid.uuid4(),
        "title": "Diwali collection teaser",
        "content_type": "post",
        "platform": "instagram",
    }
    data.update(overrides)
    return data


def test_minimal_payload_applies_defaults():
    item = ContentCalendarItemCreate(**_payload())

    assert item.status.value == "draft"
    assert item.ai_generated is False
    assert item.social_connection_id is None
    assert item.caption is None
    assert item.hashtags is None
    assert item.scheduled_datetime is None


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        ContentCalendarItemCreate(**_payload(not_a_real_field="x"))


def test_missing_title_rejected():
    payload = _payload()
    del payload["title"]
    with pytest.raises(ValidationError):
        ContentCalendarItemCreate(**payload)


def test_blank_title_rejected():
    with pytest.raises(ValidationError):
        ContentCalendarItemCreate(**_payload(title="   "))


def test_missing_content_type_rejected():
    payload = _payload()
    del payload["content_type"]
    with pytest.raises(ValidationError):
        ContentCalendarItemCreate(**payload)


def test_invalid_content_type_rejected():
    with pytest.raises(ValidationError):
        ContentCalendarItemCreate(**_payload(content_type="tweet"))


def test_invalid_platform_rejected():
    with pytest.raises(ValidationError):
        ContentCalendarItemCreate(**_payload(platform="twitter"))


@pytest.mark.parametrize("field", ["caption", "image_prompt", "call_to_action"])
def test_blank_optional_text_fields_normalize_to_none(field):
    item = ContentCalendarItemCreate(**_payload(**{field: "   "}))
    assert getattr(item, field) is None


def test_hashtags_get_hash_prefix_added_when_missing():
    item = ContentCalendarItemCreate(
        **_payload(hashtags=["handmade", "#sale", "  diwali  "])
    )
    assert item.hashtags == ["#handmade", "#sale", "#diwali"]


def test_blank_hashtags_are_dropped():
    item = ContentCalendarItemCreate(**_payload(hashtags=["#sale", "   ", ""]))
    assert item.hashtags == ["#sale"]


def test_all_blank_hashtags_normalize_to_none():
    item = ContentCalendarItemCreate(**_payload(hashtags=["   ", ""]))
    assert item.hashtags is None


def test_update_schema_allows_all_fields_omitted():
    update = ContentCalendarItemUpdate()
    assert update.model_dump(exclude_unset=True) == {}


def test_update_schema_rejects_explicit_null_for_not_null_column():
    with pytest.raises(ValidationError):
        ContentCalendarItemUpdate(status=None)


def test_update_schema_tracks_only_provided_fields():
    update = ContentCalendarItemUpdate(caption="New caption")
    assert update.model_dump(exclude_unset=True) == {"caption": "New caption"}


def test_update_schema_allows_title_content_type_platform_to_be_omitted():
    update = ContentCalendarItemUpdate(caption="Updated")
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {"caption": "Updated"}
