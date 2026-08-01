"""Pydantic schema for Analytics narration.

`MetricsRows` stands in for what a repository/aggregation query layer
would return — no DB access exists yet (see the module docstring in
facts.py), so callers pass in already-seeded metrics directly.
`AnalyticsSummary` is the final LLM-narrated output.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.ai.forecasting.schemas import RunRatePoint, UsagePoint


class ProductSales(BaseModel):
    name: str
    units_sold: int
    revenue: float


class InventoryUsage(BaseModel):
    item_name: str
    current_quantity: float
    usage: list[UsagePoint] = Field(default_factory=list)


class MetricsRows(BaseModel):
    """Seeded, already-fetched metrics for one business. Assumes seeded
    data — this is the input a real aggregation layer would eventually
    produce, not something this module queries for itself."""

    revenue_by_period: list[RunRatePoint] = Field(
        default_factory=list, description="One total per period, e.g. weekly/monthly net revenue."
    )
    top_products: list[ProductSales] = Field(default_factory=list)
    inventory_usage: list[InventoryUsage] = Field(default_factory=list)


class TopAction(BaseModel):
    action: str
    why: str


class AnalyticsSummary(BaseModel):
    narrative: str
    highlights: list[str] = Field(default_factory=list)
    top_actions: list[TopAction] = Field(default_factory=list)
