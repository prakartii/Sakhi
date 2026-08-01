"""Unit tests for the BusinessProfile schema's defaults/contract."""

from app.ai.business.models import BusinessProfile


def test_minimal_profile_has_sensible_defaults() -> None:
    profile = BusinessProfile(
        id="abc-123",
        name="Jaipur Crochet Co.",
        business_type="handmade accessories",
        target_audience="urban fashion buyers",
        location="Jaipur",
    )

    assert profile.products == []
    assert profile.languages == []
    assert profile.goals == []
    assert profile.has_website is False
    assert profile.has_instagram is False
    assert profile.has_logo is False
    assert profile.brand_voice is None


def test_product_optional_fields_default_to_none() -> None:
    profile = BusinessProfile(
        id="abc-123",
        name="Jaipur Crochet Co.",
        business_type="handmade accessories",
        target_audience="urban fashion buyers",
        location="Jaipur",
        products=[{"name": "Crochet handbag", "description": "Handmade crochet handbag"}],
    )

    assert profile.products[0].price is None
    assert profile.products[0].category is None
