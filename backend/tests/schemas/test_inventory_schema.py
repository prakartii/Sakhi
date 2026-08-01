"""Unit tests for Inventory Pydantic validation. No DB involved."""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.inventory import (
    InventoryCreate,
    InventorySummary,
    InventoryUpdate,
    StockAdjustmentRequest,
    StockInRequest,
    StockOutRequest,
)


def _payload(**overrides) -> dict:
    data = {"business_profile_id": uuid.uuid4(), "item_name": "Handwoven Scarf"}
    data.update(overrides)
    return data


def test_minimal_payload_applies_defaults():
    item = InventoryCreate(**_payload())

    assert item.item_name == "Handwoven Scarf"
    assert item.unit == "pcs"
    assert item.reorder_level == 0
    assert item.current_quantity == 0
    assert item.is_active is True


def test_blank_item_name_rejected():
    with pytest.raises(ValidationError):
        InventoryCreate(**_payload(item_name="   "))


def test_blank_unit_rejected():
    with pytest.raises(ValidationError):
        InventoryCreate(**_payload(unit="   "))


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        InventoryCreate(**_payload(not_a_real_field="x"))


def test_negative_current_quantity_rejected():
    with pytest.raises(ValidationError):
        InventoryCreate(**_payload(current_quantity=-1))


def test_negative_reorder_level_rejected():
    with pytest.raises(ValidationError):
        InventoryCreate(**_payload(reorder_level=-1))


def test_negative_unit_cost_rejected():
    with pytest.raises(ValidationError):
        InventoryCreate(**_payload(unit_cost=-1))


def test_negative_selling_price_rejected():
    with pytest.raises(ValidationError):
        InventoryCreate(**_payload(selling_price=-1))


def test_sku_normalized_to_uppercase():
    item = InventoryCreate(**_payload(sku="abc-123"))
    assert item.sku == "ABC-123"


def test_blank_sku_normalizes_to_none():
    item = InventoryCreate(**_payload(sku="   "))
    assert item.sku is None


@pytest.mark.parametrize("field", ["category", "image_url"])
def test_blank_optional_text_fields_normalize_to_none(field):
    item = InventoryCreate(**_payload(**{field: "   "}))
    assert getattr(item, field) is None


def test_valid_image_url_accepted():
    item = InventoryCreate(**_payload(image_url="https://example.com/scarf.png"))
    assert item.image_url == "https://example.com/scarf.png"


def test_invalid_image_url_rejected():
    with pytest.raises(ValidationError):
        InventoryCreate(**_payload(image_url="not-a-url"))


def test_update_schema_allows_all_fields_omitted():
    update = InventoryUpdate()
    assert update.model_dump(exclude_unset=True) == {}


def test_update_schema_has_no_current_quantity_field():
    assert "current_quantity" not in InventoryUpdate.model_fields


def test_update_schema_tracks_only_provided_fields():
    update = InventoryUpdate(category="Textiles")
    assert update.model_dump(exclude_unset=True) == {"category": "Textiles"}


# -- stock operation request schemas -----------------------------------------


def test_stock_in_requires_positive_quantity():
    with pytest.raises(ValidationError):
        StockInRequest(quantity=0)
    with pytest.raises(ValidationError):
        StockInRequest(quantity=-5)


def test_stock_in_accepts_positive_quantity():
    request = StockInRequest(quantity=10, notes="Restocked from supplier")
    assert request.quantity == 10


def test_stock_out_requires_positive_quantity():
    with pytest.raises(ValidationError):
        StockOutRequest(quantity=0)


def test_stock_adjustment_allows_zero_but_not_negative():
    StockAdjustmentRequest(new_quantity=0)  # should not raise
    with pytest.raises(ValidationError):
        StockAdjustmentRequest(new_quantity=-1)


def test_inventory_summary_requires_all_fields():
    summary = InventorySummary(
        business_profile_id=uuid.uuid4(),
        total_products=5,
        total_stock_value=1234.56,
        low_stock_count=1,
        out_of_stock_count=0,
    )
    assert summary.total_products == 5
