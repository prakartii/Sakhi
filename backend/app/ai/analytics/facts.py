"""Turns MetricsRows into plain-English fact strings, computed entirely
via app.ai.forecasting — no LLM, no randomness, independently testable
with no provider at all. summarizer.py's LLM call is only allowed to
narrate these facts, never invent numbers of its own.
"""

from __future__ import annotations

from datetime import date

from app.ai.analytics.models import InventoryUsage, MetricsRows, ProductSales
from app.ai.forecasting.run_rate import forecast_run_rate
from app.ai.forecasting.schemas import RunRatePoint
from app.ai.forecasting.stockout import forecast_stockout

_TOP_PRODUCTS_LIMIT = 3


def build_facts(metrics: MetricsRows, *, as_of: date | None = None) -> list[str]:
    """Aggregate `metrics` into fact strings ready to hand to an LLM for
    narration. `as_of` anchors stockout projections (default: today) —
    exposed mainly so tests/backtests can pin a fixed date rather than
    depending on the wall clock. Never returns an empty list — falls back
    to a single "no data" fact so summarize() always has something to
    narrate from.
    """
    facts = [
        *_revenue_facts(metrics.revenue_by_period),
        *_product_facts(metrics.top_products),
        *_stockout_facts(metrics.inventory_usage, as_of=as_of),
    ]
    return facts or ["No metrics data is available yet."]


def _revenue_facts(revenue_by_period: list[RunRatePoint]) -> list[str]:
    if len(revenue_by_period) < 2:
        return [] if not revenue_by_period else ["Not enough revenue history yet to compute a trend."]

    forecast = forecast_run_rate(revenue_by_period, periods_ahead=1)
    if forecast.trend_per_period > 0:
        trend_word = "rising"
    elif forecast.trend_per_period < 0:
        trend_word = "falling"
    else:
        trend_word = "flat"

    latest = revenue_by_period[-1].value
    return [
        f"Revenue trend is {trend_word}: latest period {latest:.0f}, moving average "
        f"{forecast.moving_average:.0f}, projected next period {forecast.projected_next_value:.0f} "
        f"(trend confidence {forecast.confidence_score:.0f}%)."
    ]


def _product_facts(top_products: list[ProductSales]) -> list[str]:
    ranked = sorted(top_products, key=lambda p: p.revenue, reverse=True)[:_TOP_PRODUCTS_LIMIT]
    return [f"{p.name}: {p.units_sold} units sold, revenue {p.revenue:.0f}." for p in ranked]


def _stockout_facts(inventory_usage: list[InventoryUsage], *, as_of: date | None) -> list[str]:
    facts = []
    for item in inventory_usage:
        forecast = forecast_stockout(item.usage, current_quantity=item.current_quantity, as_of=as_of)
        if not forecast.has_sufficient_data:
            facts.append(f"{item.item_name}: not enough usage history yet to project a stockout date.")
        elif forecast.projected_stockout_date is not None:
            facts.append(
                f"{item.item_name}: projected to run out on "
                f"{forecast.projected_stockout_date.isoformat()} "
                f"(daily usage {forecast.daily_run_rate:.2f})."
            )
        else:
            facts.append(f"{item.item_name}: stable, not currently at risk of running out.")
    return facts
