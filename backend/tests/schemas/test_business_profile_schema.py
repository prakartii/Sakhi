"""Unit tests for Business Profile Pydantic validation. No DB involved."""

import uuid

import pytest
from pydantic import ValidationError

from app.models.enums import BusinessStage
from app.schemas.business_profile import (
    BusinessProfileCreate,
    BusinessProfileOnboardingStatus,
    BusinessProfilePut,
    BusinessProfileUpdate,
)


def _payload(**overrides) -> dict:
    data = {"user_id": uuid.uuid4(), "business_name": "Anita's Boutique"}
    data.update(overrides)
    return data


def test_minimal_payload_applies_defaults():
    profile = BusinessProfileCreate(**_payload())

    assert profile.business_name == "Anita's Boutique"
    assert profile.country == "India"
    assert profile.is_primary is True
    assert profile.status.value == "active"
    assert profile.registration_type.value == "unregistered"


def test_blank_business_name_rejected():
    with pytest.raises(ValidationError):
        BusinessProfileCreate(**_payload(business_name="   "))


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        BusinessProfileCreate(**_payload(not_a_real_field="x"))


@pytest.mark.parametrize("gstin", ["27AAAPL1234C1Z5", "07AABCU9603R1ZM"])
def test_valid_gstin_accepted(gstin):
    profile = BusinessProfileCreate(**_payload(gstin=gstin))
    assert profile.gstin == gstin


@pytest.mark.parametrize("gstin", ["not-a-gstin", "27AAAPL1234C1Z", "27aaapl1234c1z5x"])
def test_invalid_gstin_rejected(gstin):
    with pytest.raises(ValidationError):
        BusinessProfileCreate(**_payload(gstin=gstin))


def test_gstin_is_normalized_to_uppercase():
    profile = BusinessProfileCreate(**_payload(gstin=" 27aaapl1234c1z5 "))
    assert profile.gstin == "27AAAPL1234C1Z5"


def test_valid_pan_accepted():
    profile = BusinessProfileCreate(**_payload(pan="ABCDE1234F"))
    assert profile.pan == "ABCDE1234F"


@pytest.mark.parametrize("pan", ["12345", "ABCDE12345", "abcde1234f1"])
def test_invalid_pan_rejected(pan):
    with pytest.raises(ValidationError):
        BusinessProfileCreate(**_payload(pan=pan))


def test_valid_pincode_accepted():
    profile = BusinessProfileCreate(**_payload(pincode="560001"))
    assert profile.pincode == "560001"


@pytest.mark.parametrize("pincode", ["12AB56", "000001", "1234"])
def test_invalid_pincode_rejected(pincode):
    with pytest.raises(ValidationError):
        BusinessProfileCreate(**_payload(pincode=pincode))


def test_year_established_out_of_range_rejected():
    with pytest.raises(ValidationError):
        BusinessProfileCreate(**_payload(year_established=1800))


def test_year_established_in_range_accepted():
    profile = BusinessProfileCreate(**_payload(year_established=2020))
    assert profile.year_established == 2020


def test_update_schema_allows_all_fields_omitted():
    update = BusinessProfileUpdate()
    assert update.model_dump(exclude_unset=True) == {}


def test_update_schema_rejects_explicit_null_for_not_null_column():
    with pytest.raises(ValidationError):
        BusinessProfileUpdate(status=None)


def test_update_schema_tracks_only_provided_fields():
    update = BusinessProfileUpdate(business_name="New Name")
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {"business_name": "New Name"}


# -- onboarding / growth-workflow fields -------------------------------------


def test_onboarding_fields_accepted():
    profile = BusinessProfileCreate(
        **_payload(
            owner_name="Anita Rao",
            business_description="Handmade boutique clothing.",
            target_audience="Working women, 25-45",
            products_or_services="Custom tailoring, alterations",
            business_stage="growing",
            website_url="https://anitasboutique.example.com",
            instagram_url="https://instagram.com/anitasboutique",
        )
    )
    assert profile.owner_name == "Anita Rao"
    assert profile.business_stage == BusinessStage.GROWING
    assert profile.website_url == "https://anitasboutique.example.com"


@pytest.mark.parametrize(
    "field",
    ["owner_name", "business_description", "target_audience", "products_or_services"],
)
def test_blank_optional_text_fields_normalize_to_none(field):
    profile = BusinessProfileCreate(**_payload(**{field: "   "}))
    assert getattr(profile, field) is None


def test_invalid_business_stage_rejected():
    with pytest.raises(ValidationError):
        BusinessProfileCreate(**_payload(business_stage="thriving"))


@pytest.mark.parametrize(
    "field", ["website_url", "instagram_url", "facebook_url", "linkedin_url"]
)
def test_valid_url_accepted(field):
    profile = BusinessProfileCreate(**_payload(**{field: "https://example.com/page"}))
    assert getattr(profile, field) == "https://example.com/page"


@pytest.mark.parametrize(
    "field", ["website_url", "instagram_url", "facebook_url", "linkedin_url"]
)
def test_invalid_url_rejected(field):
    with pytest.raises(ValidationError):
        BusinessProfileCreate(**_payload(**{field: "not-a-url"}))


def test_put_schema_requires_business_name():
    with pytest.raises(ValidationError):
        BusinessProfilePut(owner_name="Anita Rao")


def test_put_schema_applies_defaults_for_omitted_fields():
    put = BusinessProfilePut(business_name="Anita's Boutique")
    assert put.country == "India"
    assert put.owner_name is None
    assert put.is_primary is True


def test_onboarding_status_schema_validates_percentage_bounds():
    with pytest.raises(ValidationError):
        BusinessProfileOnboardingStatus(
            business_profile_id=uuid.uuid4(),
            is_complete=False,
            completion_percentage=150,
            completed_fields=[],
            missing_fields=[],
        )
