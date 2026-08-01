"""Unit tests for forecast_run_rate(), including edge cases: too little
data to fit a trend, and inputs that could otherwise divide by zero."""

from datetime import date

import pytest

from app.ai.forecasting.run_rate import forecast_run_rate
from app.ai.forecasting.schemas import RunRatePoint


def test_rising_series_projects_forward() -> None:
    points = [
        RunRatePoint(period_start=date(2026, m, 1), value=v)
        for m, v in zip(range(2, 8), [12000, 14500, 17000, 19500, 21340, 24000])
    ]

    result = forecast_run_rate(points, periods_ahead=2)

    assert result.trend_per_period > 0
    assert result.projected_next_value > points[-1].value
    assert len(result.projected_periods) == 2
    assert result.confidence_score > 90  # near-linear series


def test_flat_series_has_zero_trend_and_full_confidence() -> None:
    points = [RunRatePoint(period_start=date(2026, m, 1), value=10000) for m in range(1, 5)]

    result = forecast_run_rate(points, periods_ahead=1)

    assert result.trend_per_period == pytest.approx(0.0)
    assert result.projected_next_value == pytest.approx(10000)
    assert result.confidence_score == pytest.approx(100.0)


# --- Edge case: not enough data to fit a trend ---


def test_empty_input_raises_instead_of_guessing() -> None:
    with pytest.raises(ValueError):
        forecast_run_rate([], periods_ahead=1)


def test_single_point_raises_instead_of_guessing() -> None:
    with pytest.raises(ValueError):
        forecast_run_rate([RunRatePoint(period_start=date(2026, 1, 1), value=1000)])


def test_minimum_two_points_does_not_crash() -> None:
    points = [
        RunRatePoint(period_start=date(2026, 1, 1), value=1000),
        RunRatePoint(period_start=date(2026, 2, 1), value=1200),
    ]

    result = forecast_run_rate(points, periods_ahead=1)

    assert result.trend_per_period == pytest.approx(200.0)
    assert result.projected_next_value == pytest.approx(1400.0)


def test_periods_ahead_must_be_at_least_one() -> None:
    points = [
        RunRatePoint(period_start=date(2026, 1, 1), value=1000),
        RunRatePoint(period_start=date(2026, 2, 1), value=1200),
    ]

    with pytest.raises(ValueError):
        forecast_run_rate(points, periods_ahead=0)


def test_moving_average_window_larger_than_data_uses_all_points() -> None:
    points = [
        RunRatePoint(period_start=date(2026, 1, 1), value=1000),
        RunRatePoint(period_start=date(2026, 2, 1), value=2000),
    ]

    result = forecast_run_rate(points, periods_ahead=1, moving_average_window=10)

    assert result.moving_average == pytest.approx(1500.0)


def test_unordered_input_is_sorted_before_fitting() -> None:
    points = [
        RunRatePoint(period_start=date(2026, 3, 1), value=3000),
        RunRatePoint(period_start=date(2026, 1, 1), value=1000),
        RunRatePoint(period_start=date(2026, 2, 1), value=2000),
    ]

    result = forecast_run_rate(points, periods_ahead=1)

    assert result.trend_per_period == pytest.approx(1000.0)
    # Median gap is (31 + 28) / 2 = 29.5 days; date + timedelta only advances
    # by whole days, so this lands on Mar 1 + 29 days, not Apr 1.
    assert result.projected_periods[0].period_start == date(2026, 3, 30)
