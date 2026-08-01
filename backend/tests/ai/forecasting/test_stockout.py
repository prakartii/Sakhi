"""Unit tests for forecast_stockout(), including the edge cases that could
silently break run-rate math: no history, a single data point, and an item
with recorded days but zero consumption."""

from datetime import date, timedelta

import pytest

from app.ai.forecasting.schemas import UsagePoint
from app.ai.forecasting.stockout import forecast_stockout

TODAY = date(2026, 8, 1)


def usage_series(quantity: float, days: int, *, end: date = TODAY) -> list[UsagePoint]:
    return [
        UsagePoint(movement_date=end - timedelta(days=i), quantity=quantity) for i in range(days)
    ]


# --- Regular case, for a sanity baseline the edge cases are compared against ---


def test_regular_series_projects_a_stockout_date() -> None:
    usage = usage_series(5.1, 14)

    result = forecast_stockout(usage, current_quantity=28, window_days=14, as_of=TODAY)

    assert result.has_sufficient_data is True
    assert result.daily_run_rate == pytest.approx(5.1)
    assert result.days_of_stock_remaining == pytest.approx(28 / 5.1, abs=0.1)
    assert result.projected_stockout_date is not None
    assert result.projected_stockout_date > TODAY
    assert result.confidence_score > 0


def test_sparse_usage_uses_total_over_window_not_average_of_points() -> None:
    # Only 2 of 14 days have a recorded sale — the rate must be pulled down
    # by the empty days, not computed as if only sale-days existed.
    usage = [
        UsagePoint(movement_date=TODAY, quantity=10),
        UsagePoint(movement_date=TODAY - timedelta(days=13), quantity=10),
    ]

    result = forecast_stockout(usage, current_quantity=100, window_days=14, as_of=TODAY)

    assert result.has_sufficient_data is True
    assert result.daily_run_rate == pytest.approx(20 / 14, abs=1e-3)


# --- Edge case 1: zero sales history (no movement rows at all) ---


def test_zero_sales_history_returns_insufficient_data_not_a_crash() -> None:
    result = forecast_stockout([], current_quantity=50, as_of=TODAY)

    assert result.has_sufficient_data is False
    assert result.daily_run_rate == 0.0
    assert result.days_of_stock_remaining is None
    assert result.projected_stockout_date is None
    assert result.reorder_by_date is None
    assert result.confidence_score == 0.0


def test_usage_entirely_outside_the_window_is_treated_as_no_history() -> None:
    stale = [UsagePoint(movement_date=TODAY - timedelta(days=100), quantity=5)]

    result = forecast_stockout(stale, current_quantity=50, window_days=14, as_of=TODAY)

    assert result.has_sufficient_data is False
    assert result.projected_stockout_date is None


# --- Edge case 2: brand-new product with a single data point ---


def test_single_data_point_reports_raw_rate_but_withholds_a_date() -> None:
    usage = [UsagePoint(movement_date=TODAY, quantity=12)]

    result = forecast_stockout(usage, current_quantity=50, as_of=TODAY)

    assert result.has_sufficient_data is False
    # The raw observation is still surfaced (not hidden), just not projected from.
    assert result.daily_run_rate == pytest.approx(12.0)
    assert result.days_of_stock_remaining is None
    assert result.projected_stockout_date is None
    assert result.reorder_by_date is None
    assert result.confidence_score == 0.0


def test_two_data_points_is_enough_to_project() -> None:
    usage = [
        UsagePoint(movement_date=TODAY, quantity=10),
        UsagePoint(movement_date=TODAY - timedelta(days=1), quantity=10),
    ]

    result = forecast_stockout(usage, current_quantity=50, as_of=TODAY)

    assert result.has_sufficient_data is True
    assert result.projected_stockout_date is not None


# --- Edge case 3: a product with recorded days but no actual movement ---


def test_no_movement_with_enough_history_means_never_stocks_out() -> None:
    # Distinct from "no data": we *do* know it isn't selling, so confidence
    # should reflect real (if boring) information, not read as unknown.
    usage = usage_series(0.0, 5)

    result = forecast_stockout(usage, current_quantity=50, window_days=14, as_of=TODAY)

    assert result.has_sufficient_data is True
    assert result.daily_run_rate == 0.0
    assert result.days_of_stock_remaining is None
    assert result.projected_stockout_date is None
    assert result.reorder_by_date is None
    assert result.confidence_score > 0.0


# --- Already stocked out ---


def test_current_quantity_already_zero_projects_immediate_stockout() -> None:
    usage = usage_series(5.0, 14)

    result = forecast_stockout(usage, current_quantity=0, window_days=14, lead_time_days=5, as_of=TODAY)

    assert result.has_sufficient_data is True
    assert result.days_of_stock_remaining == 0.0
    assert result.projected_stockout_date == TODAY
    assert result.reorder_by_date == TODAY


# --- reorder_by_date only appears when a lead time is given ---


def test_reorder_by_date_is_none_without_a_lead_time() -> None:
    usage = usage_series(5.0, 14)

    result = forecast_stockout(usage, current_quantity=28, window_days=14, as_of=TODAY)

    assert result.reorder_by_date is None


def test_reorder_by_date_precedes_stockout_date_when_lead_time_given() -> None:
    usage = usage_series(5.0, 14)

    result = forecast_stockout(
        usage, current_quantity=28, window_days=14, lead_time_days=9, as_of=TODAY
    )

    assert result.reorder_by_date is not None
    assert result.reorder_by_date < result.projected_stockout_date
