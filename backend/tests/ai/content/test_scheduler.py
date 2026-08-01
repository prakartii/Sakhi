"""Unit tests for schedule_month() — pure rule-based logic, no LLM/
provider involved at all."""

from datetime import date, time

import pytest

from app.ai.content.scheduler import schedule_month


def test_all_slots_fall_within_the_requested_month() -> None:
    slots = schedule_month(date(2026, 8, 1), ["instagram"])

    assert all(s.date.year == 2026 and s.date.month == 8 for s in slots)


def test_only_year_and_month_of_the_input_date_matter() -> None:
    slots_from_first = schedule_month(date(2026, 8, 1), ["instagram"])
    slots_from_last = schedule_month(date(2026, 8, 28), ["instagram"])

    assert slots_from_first == slots_from_last


def test_posts_per_week_roughly_controls_volume() -> None:
    light = schedule_month(date(2026, 8, 1), ["instagram"], posts_per_week=1)
    heavy = schedule_month(date(2026, 8, 1), ["instagram"], posts_per_week=5)

    assert len(heavy) > len(light)


def test_cycles_through_all_given_platforms() -> None:
    slots = schedule_month(date(2026, 8, 1), ["instagram", "facebook"], posts_per_week=5)

    platforms_used = {s.platform for s in slots}
    assert platforms_used == {"instagram", "facebook"}


def test_platform_specific_post_times_are_applied() -> None:
    slots = schedule_month(date(2026, 8, 1), ["instagram", "facebook"], posts_per_week=5)

    instagram_times = {s.post_time for s in slots if s.platform == "instagram"}
    facebook_times = {s.post_time for s in slots if s.platform == "facebook"}
    assert instagram_times == {time(19, 0)}
    assert facebook_times == {time(13, 0)}


def test_marks_fixed_date_festivals_in_range() -> None:
    slots = schedule_month(date(2026, 8, 1), ["instagram"], posts_per_week=7)

    festival_dates = {s.date: s.festival for s in slots if s.festival}
    assert festival_dates.get(date(2026, 8, 15)) == "Independence Day"


def test_is_fully_deterministic() -> None:
    first = schedule_month(date(2026, 8, 1), ["instagram", "facebook"], posts_per_week=3)
    second = schedule_month(date(2026, 8, 1), ["instagram", "facebook"], posts_per_week=3)

    assert first == second


def test_rejects_empty_platforms() -> None:
    with pytest.raises(ValueError):
        schedule_month(date(2026, 8, 1), [])


def test_rejects_non_positive_posts_per_week() -> None:
    with pytest.raises(ValueError):
        schedule_month(date(2026, 8, 1), ["instagram"], posts_per_week=0)
