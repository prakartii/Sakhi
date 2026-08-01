"""Pydantic schemas for the forecasting layer. Pure deterministic math over
already-fetched transaction/inventory data — no LLM involvement (see
app.ai.forecasting's module docstring). Output shapes are designed to slot
directly into forecast_history.predicted_values / confidence_score (see
supabase/migrations/16_forecast_and_notifications.sql).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class UsagePoint(BaseModel):
    """One inventory_movements-derived data point: net units consumed
    (sales + wastage - returns) on a single date. Restocks are excluded —
    this feeds a *consumption* run-rate, not net stock change."""

    movement_date: date
    quantity: float = Field(..., ge=0)


class StockoutForecast(BaseModel):
    has_sufficient_data: bool = Field(
        ...,
        description="False when there are fewer than 2 distinct days of consumption history in "
        "the window — too little to establish a rate. daily_run_rate may still report a raw "
        "single-day observation, but projected_stockout_date/reorder_by_date are withheld rather "
        "than presenting an anecdote as a forecast.",
    )
    daily_run_rate: float = Field(..., description="Consumption per day, averaged over the lookback window.")
    days_of_stock_remaining: float | None = Field(
        default=None, description="current_quantity / daily_run_rate; null if run rate is 0."
    )
    projected_stockout_date: date | None = None
    reorder_by_date: date | None = Field(
        default=None, description="projected_stockout_date minus supplier lead time, if lead_time_days was given."
    )
    confidence_score: float = Field(
        ..., ge=0, le=100, description="Higher with more window coverage and lower day-to-day variance."
    )


class RunRatePoint(BaseModel):
    """One aggregated period total, e.g. a month's net cashflow or revenue."""

    period_start: date
    value: float


class RunRateForecast(BaseModel):
    period_days: int = Field(..., description="Inferred length of one period, in days (median gap between input points).")
    moving_average: float
    trend_per_period: float = Field(..., description="Linear-regression slope: average change in value per period.")
    projected_next_value: float
    projected_periods: list[RunRatePoint] = Field(default_factory=list)
    confidence_score: float = Field(
        ..., ge=0, le=100, description="Linear fit quality (R^2) against the input points, as a 0-100 score."
    )
