"""Response schemas for GET /business-profiles/{id}/ai-summary,
GET /business-profiles/{id}/growth-forecast, and
GET /business-profiles/{id}/noticed-summary."""

import uuid
from datetime import date

from pydantic import BaseModel


class TopActionOut(BaseModel):
    action: str
    why: str


class AISummaryResponse(BaseModel):
    narrative: str
    highlights: list[str]
    top_actions: list[TopActionOut]


class RunRatePointOut(BaseModel):
    period_start: date
    value: float


class GrowthForecastResponse(BaseModel):
    """Deterministic linear-trend projection over logged weekly revenue —
    app.ai.forecasting.run_rate, no LLM for the numbers themselves; why/
    basis narrate the already-computed trend, same "the model never does
    the math" principle as every other forecast in this app."""

    has_sufficient_data: bool
    historical: list[RunRatePointOut]
    projected: list[RunRatePointOut]
    moving_average: float | None = None
    trend_per_period: float | None = None
    confidence_score: float | None = None
    why: str | None = None
    basis: str | None = None


class StockSignalOut(BaseModel):
    inventory_id: uuid.UUID
    item_name: str
    days_remaining: int
    current_quantity: float
    unit: str


class MemorySignalOut(BaseModel):
    business_memory_id: uuid.UUID
    title: str | None
    content: str


class NoticedSummaryResponse(BaseModel):
    """Cross-module proactive signals — deliberately excludes scheme
    matches (that's what GET /schemes/matches is for). The one thing this
    endpoint does that no single-domain endpoint can: connected_why/
    connected_basis narrate how signals from *different* modules relate to
    each other in the same week, when there's more than one to connect."""

    stock_signals: list[StockSignalOut]
    revenue_trend_per_week: float | None
    revenue_declining: bool
    memory_signals: list[MemorySignalOut]
    connected_why: str | None = None
    connected_basis: str | None = None
