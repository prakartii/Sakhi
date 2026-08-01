"""Run-rate / moving-average stockout forecasting — deterministic math over
inventory_movements-derived consumption data. Backs the Smart Inventory
"runs out in ~N days" / reorder-by-date cards.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean, pstdev

from app.ai.forecasting.schemas import StockoutForecast, UsagePoint

DEFAULT_WINDOW_DAYS = 14
MIN_DISTINCT_DAYS = 2


def forecast_stockout(
    usage: list[UsagePoint],
    *,
    current_quantity: float,
    window_days: int = DEFAULT_WINDOW_DAYS,
    lead_time_days: int | None = None,
    as_of: date | None = None,
) -> StockoutForecast:
    """Project when `current_quantity` runs out, from a run-rate over the
    last `window_days` of consumption in `usage`.

    The run rate is total consumed / window length in days (not average of
    the given points), so gaps where nothing sold on a given day correctly
    pull the rate down rather than being silently skipped. `usage` may
    contain any subset of dates within the window — days with no movement
    just aren't in the list.

    With fewer than 2 distinct days of data (no history, or a single
    observation), there isn't enough to project a date from — the result
    has `has_sufficient_data=False` and no projected_stockout_date/
    reorder_by_date, rather than extrapolating a rate from one data point.
    """
    today = as_of or date.today()
    window_start = today - timedelta(days=window_days - 1)
    recent = [p for p in usage if window_start <= p.movement_date <= today]

    if not recent:
        # Zero sales history / no movement at all — nothing to extrapolate from.
        return StockoutForecast(has_sufficient_data=False, daily_run_rate=0.0, confidence_score=0.0)

    daily_totals = _daily_totals(recent)
    if len(daily_totals) < MIN_DISTINCT_DAYS:
        # A brand-new product with a single day of data can't establish a
        # rate — report it as a raw observation but withhold a projected
        # date rather than presenting an anecdote as a forecast.
        raw_rate = sum(daily_totals.values()) / len(daily_totals)
        return StockoutForecast(
            has_sufficient_data=False,
            daily_run_rate=round(raw_rate, 3),
            confidence_score=0.0,
        )

    earliest = min(daily_totals)
    span_days = min((today - earliest).days + 1, window_days)
    daily_run_rate = sum(daily_totals.values()) / span_days
    confidence = _confidence(list(daily_totals.values()), coverage=span_days / window_days)

    if daily_run_rate <= 0:
        # Enough history to be confident it isn't moving, not just missing data.
        return StockoutForecast(has_sufficient_data=True, daily_run_rate=0.0, confidence_score=confidence)

    if current_quantity <= 0:
        return StockoutForecast(
            has_sufficient_data=True,
            daily_run_rate=round(daily_run_rate, 3),
            days_of_stock_remaining=0.0,
            projected_stockout_date=today,
            reorder_by_date=today,
            confidence_score=confidence,
        )

    days_remaining = current_quantity / daily_run_rate
    stockout_date = today + timedelta(days=days_remaining)
    reorder_by = (
        stockout_date - timedelta(days=lead_time_days) if lead_time_days is not None else None
    )

    return StockoutForecast(
        has_sufficient_data=True,
        daily_run_rate=round(daily_run_rate, 3),
        days_of_stock_remaining=round(days_remaining, 1),
        projected_stockout_date=stockout_date,
        reorder_by_date=reorder_by,
        confidence_score=confidence,
    )


def _daily_totals(points: list[UsagePoint]) -> dict[date, float]:
    totals: dict[date, float] = defaultdict(float)
    for point in points:
        totals[point.movement_date] += point.quantity
    return dict(totals)


def _confidence(daily_values: list[float], *, coverage: float) -> float:
    """Heuristic, deterministic confidence: more of the window covered by
    data, and lower day-to-day variance relative to the mean, both raise
    confidence. Not a statistical guarantee — a relative ranking signal."""
    if not daily_values:
        return 0.0
    avg = mean(daily_values)
    if len(daily_values) < 2 or avg == 0:
        variance_penalty = 0.0
    else:
        variance_penalty = min(pstdev(daily_values) / avg, 1.0)
    score = coverage * (1 - 0.5 * variance_penalty)
    return round(max(0.0, min(score, 1.0)) * 100, 1)
