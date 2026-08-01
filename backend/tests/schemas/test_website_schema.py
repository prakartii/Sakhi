"""Unit tests for Website Pydantic validation. No DB involved."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.website import WebsiteCreate, WebsiteUpdate


def _payload(**overrides) -> dict:
    data = {"business_profile_id": uuid.uuid4(), "website_name": "AnitaWeaves Store"}
    data.update(overrides)
    return data


def test_minimal_payload_applies_defaults():
    website = WebsiteCreate(**_payload())

    assert website.website_name == "AnitaWeaves Store"
    assert website.status.value == "draft"
    assert website.published is False


def test_blank_website_name_rejected():
    with pytest.raises(ValidationError):
        WebsiteCreate(**_payload(website_name="   "))


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        WebsiteCreate(**_payload(not_a_real_field="x"))


@pytest.mark.parametrize(
    "field", ["github_repository", "template", "seo_title", "seo_description"]
)
def test_blank_optional_text_fields_normalize_to_none(field):
    website = WebsiteCreate(**_payload(**{field: "   "}))
    assert getattr(website, field) is None


def test_github_repository_shorthand_accepted():
    website = WebsiteCreate(**_payload(github_repository="anita/weaves-store"))
    assert website.github_repository == "anita/weaves-store"


@pytest.mark.parametrize("field", ["deployment_url", "favicon"])
def test_valid_url_accepted(field):
    website = WebsiteCreate(**_payload(**{field: "https://example.com/asset.png"}))
    assert getattr(website, field) == "https://example.com/asset.png"


@pytest.mark.parametrize("field", ["deployment_url", "favicon"])
def test_invalid_url_rejected(field):
    with pytest.raises(ValidationError):
        WebsiteCreate(**_payload(**{field: "not-a-url"}))


def test_valid_custom_domain_accepted_and_lowercased():
    website = WebsiteCreate(**_payload(custom_domain="Shop.AnitaWeaves.com"))
    assert website.custom_domain == "shop.anitaweaves.com"


@pytest.mark.parametrize(
    "domain", ["not a domain", "https://example.com", "example", "example.c"]
)
def test_invalid_custom_domain_rejected(domain):
    with pytest.raises(ValidationError):
        WebsiteCreate(**_payload(custom_domain=domain))


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        WebsiteCreate(**_payload(status="thriving"))


def test_update_schema_allows_all_fields_omitted():
    update = WebsiteUpdate()
    assert update.model_dump(exclude_unset=True) == {}


def test_update_schema_rejects_explicit_null_for_not_null_column():
    with pytest.raises(ValidationError):
        WebsiteUpdate(status=None)


def test_update_schema_tracks_only_provided_fields():
    update = WebsiteUpdate(website_name="New Name")
    assert update.model_dump(exclude_unset=True) == {"website_name": "New Name"}


def test_update_schema_change_notes_is_optional_and_not_a_website_field():
    update = WebsiteUpdate(
        website_name="New Name", change_notes="Refreshed homepage copy"
    )
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {
        "website_name": "New Name",
        "change_notes": "Refreshed homepage copy",
    }
