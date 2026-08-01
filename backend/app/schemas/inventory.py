"""Pydantic v2 request/response schemas for the Inventory module.

Kept separate from app.models.inventory(_movement) (the ORM shape) on
purpose, same as every other module in this codebase: format/shape
validation (non-negative prices/quantities, URL scheme, blank-text
normalization) lives here at the API boundary. Rules that require
interpreting the data — a supplier_id that doesn't exist, a stock-out that
would go negative — belong in the service layer instead; see
InventoryService.

InventoryUpdate deliberately has no `current_quantity` field: PATCH cannot
change stock on hand. Every quantity change goes through stock_in/
stock_out/adjust_stock instead, so every change is captured as an
inventory_movements row — see InventoryService for why that's the point.
"""

import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import InventoryMovementType

_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
_BLANK_TO_NONE_FIELDS = ("sku", "category", "image_url")


class InventoryBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    item_name: Annotated[str, Field(min_length=1, max_length=200)]
    sku: Annotated[str | None, Field(max_length=50)] = None
    category: Annotated[str | None, Field(max_length=100)] = None
    unit: Annotated[str, Field(min_length=1, max_length=20)] = "pcs"
    reorder_level: Annotated[float, Field(ge=0)] = 0
    unit_cost: Annotated[float | None, Field(ge=0)] = None
    selling_price: Annotated[float | None, Field(ge=0)] = None
    image_url: Annotated[str | None, Field(max_length=2048)] = None
    supplier_id: UUID | None = None
    is_active: bool = True

    @field_validator("item_name")
    @classmethod
    def _reject_blank_item_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("item_name cannot be blank")
        return value

    @field_validator("unit")
    @classmethod
    def _reject_blank_unit(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("unit cannot be blank")
        return value

    @field_validator("sku")
    @classmethod
    def _normalize_sku(cls, value: str | None) -> str | None:
        # Uppercased so "abc-123" and "ABC-123" collide under
        # uq_inventory_business_sku instead of silently coexisting as
        # "different" SKUs that are really the same product.
        if value is None:
            return None
        value = value.strip().upper()
        return value or None

    @field_validator(*(f for f in _BLANK_TO_NONE_FIELDS if f != "sku"))
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        return value or None

    @field_validator("image_url")
    @classmethod
    def _validate_url_scheme(cls, value: str | None) -> str | None:
        if value is not None and not _URL_PATTERN.match(value):
            raise ValueError("must be a valid URL starting with http:// or https://")
        return value


class InventoryCreate(InventoryBase):
    business_profile_id: UUID = Field(
        description="The business this product belongs to."
    )
    current_quantity: Annotated[float, Field(ge=0)] = Field(
        default=0,
        description="Starting stock on hand. Recorded as an initial "
        "'Initial stock' movement if greater than 0.",
    )


class InventoryUpdate(InventoryBase):
    """PATCH semantics: only fields explicitly present in the request body
    are applied (see InventoryService.update, which calls
    model_dump(exclude_unset=True)) — omitting a field leaves it
    unchanged. `item_name` is the only field Base requires with no
    default, so it's the only one overridden as optional here. There is
    no `current_quantity` field — see this module's docstring.
    """

    item_name: Annotated[str, Field(min_length=1, max_length=200)] | None = None


class InventoryRead(InventoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_profile_id: UUID
    current_quantity: float
    created_at: datetime
    updated_at: datetime


class InventoryListResponse(BaseModel):
    items: list[InventoryRead]
    total: int
    limit: int
    offset: int


class InventorySummary(BaseModel):
    """Response for GET /inventory/summary."""

    business_profile_id: UUID
    total_products: int
    total_stock_value: float
    low_stock_count: int
    out_of_stock_count: int


# -- stock operations -----------------------------------------------------


class StockInRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    quantity: Annotated[float, Field(gt=0)]
    notes: Annotated[str | None, Field(max_length=1000)] = None
    related_transaction_id: UUID | None = None


class StockOutRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    quantity: Annotated[float, Field(gt=0)]
    notes: Annotated[str | None, Field(max_length=1000)] = None
    related_transaction_id: UUID | None = None


class StockAdjustmentRequest(BaseModel):
    """Sets stock to an absolute known value (e.g. after a physical
    count) rather than adding/removing a delta — that's what distinguishes
    this from stock_in/stock_out."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    new_quantity: Annotated[float, Field(ge=0)]
    notes: Annotated[str | None, Field(max_length=1000)] = None


# -- movement history -------------------------------------------------------


class InventoryMovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inventory_id: UUID
    related_transaction_id: UUID | None
    movement_type: InventoryMovementType
    quantity: float
    quantity_before: float
    quantity_after: float
    notes: str | None
    movement_date: datetime
    created_at: datetime
    updated_at: datetime


class InventoryMovementListResponse(BaseModel):
    items: list[InventoryMovementRead]
    total: int
    limit: int
    offset: int
