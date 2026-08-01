"""Unit tests for should_pivot() — pure logic, no network involved."""

from app.ai.voice.pivot import should_pivot


def test_disabled_flag_never_pivots() -> None:
    assert should_pivot("hi-IN", translate_pivot_enabled=False) is False
    assert should_pivot("ta-IN", translate_pivot_enabled=False) is False


def test_enabled_flag_pivots_non_english_languages() -> None:
    assert should_pivot("hi-IN", translate_pivot_enabled=True) is True
    assert should_pivot("ta-IN", translate_pivot_enabled=True) is True
    assert should_pivot("te-IN", translate_pivot_enabled=True) is True


def test_english_never_pivots_even_if_enabled() -> None:
    assert should_pivot("en-IN", translate_pivot_enabled=True) is False
