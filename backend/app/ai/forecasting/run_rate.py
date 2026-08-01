"""Moving-average + linear-trend forecasting over a periodic time series
(e.g. monthly net cashflow, weekly revenue). Backs Cashflow Health's trend
projections (forecast_type 'cashflow' / 'revenue' in forecast_history).
"""

from __future__ import annotations

from datetime import timedelta
from statistics import mean, median

from app.ai.forecasting.schemas import RunRateForecast, RunRatePoint

DEFAULT_MOVING_AVERAGE_WINDOW = 3


def forecast_run_rate(
    points: list[RunRatePoint],
    *,
    periods_ahead: int = 1,
    moving_average_window: int = DEFAULT_MOVING_AVERAGE_WINDOW,
) -> RunRateForecast:
    """Project the next `periods_ahead` period values from a simple linear
    trend fit over `points`, plus a moving average of the most recent
    `moving_average_window` periods.

    `points` need at least 2 entries (a trend needs two points) and should
    already be one total per period (e.g. one row per month) — this
    function does no aggregation of its own. Period length is inferred as
    the median gap between consecutive `period_start` dates, so it works
    for weekly, monthly, or irregular-but-roughly-even series alike.
    """
    if len(points) < 2:
        raise ValueError("forecast_run_rate needs at least 2 data points")
    if periods_ahead < 1:
        raise ValueError("periods_ahead must be >= 1")

    ordered = sorted(points, key=lambda p: p.period_start)
    values = [p.value for p in ordered]

    window = values[-moving_average_window:]
    moving_avg = mean(window)

    slope, intercept, r_squared = _linear_regression(values)
    period_length = _infer_period_length(ordered)
    last_index = len(values) - 1
    last_date = ordered[-1].period_start

    projected_periods = [
        RunRatePoint(
            period_start=last_date + period_length * step,
            value=round(intercept + slope * (last_index + step), 2),
        )
        for step in range(1, periods_ahead + 1)
    ]

    return RunRateForecast(
        period_days=period_length.days,
        moving_average=round(moving_avg, 2),
        trend_per_period=round(slope, 2),
        projected_next_value=projected_periods[0].value,
        projected_periods=projected_periods,
        confidence_score=round(max(0.0, min(r_squared, 1.0)) * 100, 1),
    )


def _linear_regression(values: list[float]) -> tuple[float, float, float]:
    """Ordinary least squares of `values` against their index. Returns
    (slope, intercept, r_squared)."""
    n = len(values)
    xs = list(range(n))
    x_mean = mean(xs)
    y_mean = mean(values)

    ss_xx = sum((x - x_mean) ** 2 for x in xs)
    if ss_xx == 0:
        return 0.0, y_mean, 0.0

    ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean

    ss_tot = sum((y - y_mean) ** 2 for y in values)
    if ss_tot == 0:
        return slope, intercept, 1.0
    predicted = [intercept + slope * x for x in xs]
    ss_res = sum((y - yp) ** 2 for y, yp in zip(values, predicted))
    return slope, intercept, 1 - ss_res / ss_tot


def _infer_period_length(ordered: list[RunRatePoint]) -> timedelta:
    day_gaps = [(b.period_start - a.period_start).days for a, b in zip(ordered, ordered[1:])]
    return timedelta(days=median(day_gaps))
