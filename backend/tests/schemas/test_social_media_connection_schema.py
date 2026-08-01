"""Unit tests for Social Media Connection Pydantic validation. No DB
involved. In particular, these confirm SocialMediaConnectionRead has no
access_token/refresh_token field — the schema-level guarantee that a
response can never leak a stored token."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.social_media_connection import (
    RefreshTokenRequest,
    SocialMediaConnectionCreate,
    SocialMediaConnectionRead,
    SyncMetadataRequest,
)


def _payload(**overrides) -> dict:
    data = {
        "business_profile_id": uuid.uuid4(),
        "platform": "instagram",
        "access_token": "raw-access-token",
    }
    data.update(overrides)
    return data


def test_minimal_payload_applies_defaults():
    connection = SocialMediaConnectionCreate(**_payload())

    assert connection.access_token == "raw-access-token"
    assert connection.refresh_token is None
    assert connection.token_expiry is None
    assert connection.account_name is None


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        SocialMediaConnectionCreate(**_payload(not_a_real_field="x"))


def test_missing_access_token_rejected():
    payload = _payload()
    del payload["access_token"]
    with pytest.raises(ValidationError):
        SocialMediaConnectionCreate(**payload)


def test_blank_access_token_rejected():
    with pytest.raises(ValidationError):
        SocialMediaConnectionCreate(**_payload(access_token=""))


def test_missing_platform_rejected():
    payload = _payload()
    del payload["platform"]
    with pytest.raises(ValidationError):
        SocialMediaConnectionCreate(**payload)


def test_invalid_platform_rejected():
    with pytest.raises(ValidationError):
        SocialMediaConnectionCreate(**_payload(platform="twitter"))


@pytest.mark.parametrize("field", ["account_name", "account_id"])
def test_blank_optional_text_fields_normalize_to_none(field):
    connection = SocialMediaConnectionCreate(**_payload(**{field: "   "}))
    assert getattr(connection, field) is None


def test_valid_profile_url_accepted():
    connection = SocialMediaConnectionCreate(
        **_payload(profile_url="https://instagram.com/sakhi.crafts")
    )
    assert connection.profile_url == "https://instagram.com/sakhi.crafts"


def test_invalid_profile_url_rejected():
    with pytest.raises(ValidationError):
        SocialMediaConnectionCreate(**_payload(profile_url="not-a-url"))


def test_refresh_token_request_requires_access_token():
    with pytest.raises(ValidationError):
        RefreshTokenRequest()


def test_refresh_token_request_accepts_minimal_payload():
    request = RefreshTokenRequest(access_token="new-token")
    assert request.access_token == "new-token"
    assert request.refresh_token is None


def test_sync_metadata_request_allows_all_fields_omitted():
    request = SyncMetadataRequest()
    assert request.model_dump(exclude_unset=True) == {}


def test_sync_metadata_request_rejects_invalid_profile_url():
    with pytest.raises(ValidationError):
        SyncMetadataRequest(profile_url="not-a-url")


def test_sync_metadata_request_normalizes_blank_account_name():
    request = SyncMetadataRequest(account_name="   ")
    assert request.account_name is None


def test_read_schema_has_no_token_fields():
    field_names = set(SocialMediaConnectionRead.model_fields)
    assert "access_token" not in field_names
    assert "refresh_token" not in field_names


def test_read_schema_builds_from_attributes():
    class _FakeORMRow:
        id = uuid.uuid4()
        business_profile_id = uuid.uuid4()
        platform = "linkedin"
        account_name = "Sakhi Crafts"
        account_id = "12345"
        profile_url = "https://linkedin.com/company/sakhi-crafts"
        token_expiry = None
        connection_status = "connected"
        last_sync = None
        created_at = "2026-01-01T00:00:00Z"
        updated_at = "2026-01-01T00:00:00Z"
        # Even if the ORM object carries tokens (it does, in reality), the
        # response schema has no field to copy them into.
        access_token = "should-never-appear"
        refresh_token = "should-never-appear-either"

    read = SocialMediaConnectionRead.model_validate(_FakeORMRow())

    assert "should-never-appear" not in read.model_dump_json()
