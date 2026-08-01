"""Unit tests for Brand Asset Pydantic validation. No DB involved."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.brand_asset import BrandAssetCreate, BrandAssetUpdate


def _payload(**overrides) -> dict:
    data = {"business_profile_id": uuid.uuid4(), "brand_name": "AnitaWeaves"}
    data.update(overrides)
    return data


def test_minimal_payload_applies_defaults():
    asset = BrandAssetCreate(**_payload())

    assert asset.brand_name == "AnitaWeaves"
    assert asset.status.value == "draft"


def test_blank_brand_name_rejected():
    with pytest.raises(ValidationError):
        BrandAssetCreate(**_payload(brand_name="   "))


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        BrandAssetCreate(**_payload(not_a_real_field="x"))


@pytest.mark.parametrize(
    "field",
    [
        "tagline",
        "brand_story",
        "mission",
        "vision",
        "typography",
        "brand_voice",
        "packaging_notes",
    ],
)
def test_blank_optional_text_fields_normalize_to_none(field):
    asset = BrandAssetCreate(**_payload(**{field: "   "}))
    assert getattr(asset, field) is None


@pytest.mark.parametrize("color", ["#8F2F56", "#FFF", "#000000"])
def test_valid_hex_color_accepted(color):
    asset = BrandAssetCreate(**_payload(primary_color=color))
    assert asset.primary_color == color


@pytest.mark.parametrize("color", ["8F2F56", "#GGGGGG", "not-a-color", "#12"])
def test_invalid_hex_color_rejected(color):
    with pytest.raises(ValidationError):
        BrandAssetCreate(**_payload(primary_color=color))


@pytest.mark.parametrize("field", ["logo_url", "favicon_url"])
def test_valid_url_accepted(field):
    asset = BrandAssetCreate(**_payload(**{field: "https://example.com/logo.png"}))
    assert getattr(asset, field) == "https://example.com/logo.png"


@pytest.mark.parametrize("field", ["logo_url", "favicon_url"])
def test_invalid_url_rejected(field):
    with pytest.raises(ValidationError):
        BrandAssetCreate(**_payload(**{field: "not-a-url"}))


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        BrandAssetCreate(**_payload(status="thriving"))


def test_update_schema_allows_all_fields_omitted():
    update = BrandAssetUpdate()
    assert update.model_dump(exclude_unset=True) == {}


def test_update_schema_rejects_explicit_null_for_not_null_column():
    with pytest.raises(ValidationError):
        BrandAssetUpdate(status=None)


def test_update_schema_tracks_only_provided_fields():
    update = BrandAssetUpdate(brand_name="New Name")
    assert update.model_dump(exclude_unset=True) == {"brand_name": "New Name"}
