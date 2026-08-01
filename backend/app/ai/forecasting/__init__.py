"""Deterministic forecasting layer: run-rate / moving-average math over
already-fetched transaction and inventory data. No LLM involvement — per
the tech stack doc, "the LLM never does the math"; app.ai.explanations is
what turns these numbers into prose.
"""

from app.ai.forecasting.run_rate import forecast_run_rate
from app.ai.forecasting.schemas import (
    RunRateForecast,
    RunRatePoint,
    StockoutForecast,
    UsagePoint,
)
from app.ai.forecasting.stockout import forecast_stockout

__all__ = [
    "RunRateForecast",
    "RunRatePoint",
    "StockoutForecast",
    "UsagePoint",
    "forecast_run_rate",
    "forecast_stockout",
]
