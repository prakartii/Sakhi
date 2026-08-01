"""Unit tests for build_facts() — pure aggregation via app.ai.forecasting,
no LLM/provider involved at all."""

from datetime import date, timedelta

from app.ai.analytics.facts import build_facts
from app.ai.analytics.models import InventoryUsage, MetricsRows, ProductSales
from app.ai.forecasting.schemas import RunRatePoint, UsagePoint

TODAY = date(2026, 8, 1)


def test_empty_metrics_falls_back_to_a_single_no_data_fact() -> None:
    facts = build_facts(MetricsRows())

    assert facts == ["No metrics data is available yet."]


def test_single_revenue_point_reports_insufficient_history() -> None:
    metrics = MetricsRows(revenue_by_period=[RunRatePoint(period_start=date(2026, 1, 1), value=1000)])

    facts = build_facts(metrics)

    assert any("Not enough revenue history" in f for f in facts)


def test_rising_revenue_series_is_reported_as_rising() -> None:
    months = [date(2026, m, 1) for m in range(2, 8)]
    values = [12000, 14500, 17000, 19500, 21340, 24000]
    metrics = MetricsRows(
        revenue_by_period=[RunRatePoint(period_start=d, value=v) for d, v in zip(months, values)]
    )

    facts = build_facts(metrics)

    assert any("rising" in f for f in facts)


def test_falling_revenue_series_is_reported_as_falling() -> None:
    months = [date(2026, m, 1) for m in range(2, 6)]
    values = [24000, 21000, 18000, 15000]
    metrics = MetricsRows(
        revenue_by_period=[RunRatePoint(period_start=d, value=v) for d, v in zip(months, values)]
    )

    facts = build_facts(metrics)

    assert any("falling" in f for f in facts)


def test_top_products_are_ranked_by_revenue_and_capped() -> None:
    metrics = MetricsRows(
        top_products=[
            ProductSales(name="A", units_sold=1, revenue=100),
            ProductSales(name="B", units_sold=1, revenue=500),
            ProductSales(name="C", units_sold=1, revenue=300),
            ProductSales(name="D", units_sold=1, revenue=50),
        ]
    )

    facts = build_facts(metrics)
    product_facts = [f for f in facts if any(name in f for name in "ABCD")]

    assert product_facts[0].startswith("B:")
    assert product_facts[1].startswith("C:")
    assert product_facts[2].startswith("A:")
    assert not any(f.startswith("D:") for f in product_facts)  # capped to top 3


def test_inventory_with_no_history_reports_insufficient_data() -> None:
    metrics = MetricsRows(
        inventory_usage=[InventoryUsage(item_name="Indigo dye", current_quantity=10, usage=[])]
    )

    facts = build_facts(metrics, as_of=TODAY)

    assert any("Indigo dye" in f and "not enough usage history" in f for f in facts)


def test_inventory_with_active_usage_reports_a_stockout_date() -> None:
    usage = [UsagePoint(movement_date=TODAY - timedelta(days=i), quantity=5.0) for i in range(14)]
    metrics = MetricsRows(
        inventory_usage=[
            InventoryUsage(item_name="Crochet handbags", current_quantity=20, usage=usage)
        ]
    )

    facts = build_facts(metrics, as_of=TODAY)

    assert any("Crochet handbags" in f and "projected to run out on" in f for f in facts)


def test_inventory_with_zero_usage_reports_stable() -> None:
    usage = [UsagePoint(movement_date=TODAY - timedelta(days=i), quantity=0.0) for i in range(14)]
    metrics = MetricsRows(
        inventory_usage=[InventoryUsage(item_name="Packaging boxes", current_quantity=50, usage=usage)]
    )

    facts = build_facts(metrics, as_of=TODAY)

    assert any("Packaging boxes" in f and "stable" in f for f in facts)
