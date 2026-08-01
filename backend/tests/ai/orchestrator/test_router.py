"""Unit tests for route() — pure phrase-matching logic, no LLM/provider
involved at all."""

from app.ai.orchestrator.router import route


def test_sales_growth_request_pulls_in_three_services() -> None:
    assert route("I need more sales") == ["analytics", "content", "brand"]


def test_logo_request_maps_to_brand_only() -> None:
    assert route("I want a new logo") == ["brand"]


def test_website_request_maps_to_website_only() -> None:
    assert route("help me build a website") == ["website"]


def test_social_post_request_maps_to_content_only() -> None:
    assert route("write me an instagram caption") == ["content"]


def test_revenue_question_maps_to_analytics_only() -> None:
    assert route("how is my revenue doing this month") == ["analytics"]


def test_unmatched_request_falls_back_to_analytics() -> None:
    assert route("what's the weather like") == ["analytics"]


def test_matching_multiple_phrases_for_the_same_service_does_not_duplicate() -> None:
    assert route("I need a new logo and a fresh brand voice") == ["brand"]


def test_is_case_insensitive() -> None:
    assert route("I NEED MORE SALES") == ["analytics", "content", "brand"]
