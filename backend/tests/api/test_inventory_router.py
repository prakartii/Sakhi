"""Endpoint-level tests for the Inventory CRUD + stock-operations API.

InventoryService is replaced via FastAPI's dependency_overrides with an
in-memory fake, so these tests exercise routing, status codes, response
shapes, and — critically — the route-ordering fix for /low-stock,
/out-of-stock and /summary against /{inventory_id}. Uses the shared
`client` fixture from tests/conftest.py (an in-process ASGI client against
the real app).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.ai.forecasting.schemas import StockoutForecast
from app.api.v1.endpoints import inventory as endpoint_module
from app.main import app
from app.models.enums import InventoryMovementType
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.services.inventory import (
    InsufficientStockError,
    InventoryConflictError,
    InventoryNotFoundError,
    InvalidReferenceError,
)

BASE_URL = "/api/v1/inventory"


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, Inventory] = {}
        self.movements: list[InventoryMovement] = []
        self.raise_on_create: Exception | None = None
        self.raise_on_stock_out: Exception | None = None
        self.forecast_override: StockoutForecast | None = None

    async def create(self, payload):
        if self.raise_on_create:
            raise self.raise_on_create
        now = datetime.now(timezone.utc)
        item = Inventory(
            id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump()
        )
        self.store[item.id] = item
        return item

    async def get(self, inventory_id):
        item = self.store.get(inventory_id)
        if item is None:
            raise InventoryNotFoundError(str(inventory_id))
        return item

    async def list(
        self,
        business_profile_id,
        *,
        q=None,
        category=None,
        supplier_id=None,
        is_active=None,
        limit=20,
        offset=0,
    ):
        items = [
            i
            for i in self.store.values()
            if i.business_profile_id == business_profile_id
        ]
        if q:
            items = [i for i in items if q.lower() in i.item_name.lower()]
        if category is not None:
            items = [i for i in items if i.category == category]
        if supplier_id is not None:
            items = [i for i in items if i.supplier_id == supplier_id]
        if is_active is not None:
            items = [i for i in items if i.is_active == is_active]
        return items[offset : offset + limit], len(items)

    async def list_low_stock(self, business_profile_id, *, limit=20, offset=0):
        items = [
            i
            for i in self.store.values()
            if i.business_profile_id == business_profile_id
            and i.is_active
            and 0 < i.current_quantity <= i.reorder_level
        ]
        return items[offset : offset + limit], len(items)

    async def list_out_of_stock(self, business_profile_id, *, limit=20, offset=0):
        items = [
            i
            for i in self.store.values()
            if i.business_profile_id == business_profile_id
            and i.is_active
            and i.current_quantity <= 0
        ]
        return items[offset : offset + limit], len(items)

    async def get_summary(self, business_profile_id):
        items = [
            i
            for i in self.store.values()
            if i.business_profile_id == business_profile_id and i.is_active
        ]
        return {
            "business_profile_id": business_profile_id,
            "total_products": len(items),
            "total_stock_value": sum(
                i.current_quantity * (i.unit_cost or 0) for i in items
            ),
            "low_stock_count": sum(
                1 for i in items if 0 < i.current_quantity <= i.reorder_level
            ),
            "out_of_stock_count": sum(1 for i in items if i.current_quantity <= 0),
        }

    async def update(self, inventory_id, payload):
        item = await self.get(inventory_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        return item

    async def delete(self, inventory_id):
        item = await self.get(inventory_id)
        item.is_active = False

    def _record_movement(self, item, *, movement_type, quantity_before, quantity_after):
        now = datetime.now(timezone.utc)
        movement = InventoryMovement(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            inventory_id=item.id,
            related_transaction_id=None,
            movement_type=movement_type,
            quantity=abs(quantity_after - quantity_before),
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            notes=None,
            movement_date=now,
        )
        self.movements.append(movement)

    async def stock_in(self, inventory_id, payload):
        item = await self.get(inventory_id)
        before = item.current_quantity
        item.current_quantity = before + payload.quantity
        self._record_movement(
            item,
            movement_type=InventoryMovementType.RESTOCK,
            quantity_before=before,
            quantity_after=item.current_quantity,
        )
        return item

    async def stock_out(self, inventory_id, payload):
        if self.raise_on_stock_out:
            raise self.raise_on_stock_out
        item = await self.get(inventory_id)
        before = item.current_quantity
        after = before - payload.quantity
        if after < 0:
            raise InsufficientStockError("Cannot remove more than available.")
        item.current_quantity = after
        self._record_movement(
            item,
            movement_type=InventoryMovementType.SALE,
            quantity_before=before,
            quantity_after=after,
        )
        return item

    async def adjust_stock(self, inventory_id, payload):
        item = await self.get(inventory_id)
        before = item.current_quantity
        item.current_quantity = payload.new_quantity
        self._record_movement(
            item,
            movement_type=InventoryMovementType.ADJUSTMENT,
            quantity_before=before,
            quantity_after=item.current_quantity,
        )
        return item

    async def list_movements(
        self, inventory_id, *, movement_type=None, limit=20, offset=0
    ):
        await self.get(inventory_id)
        items = [m for m in reversed(self.movements) if m.inventory_id == inventory_id]
        if movement_type is not None:
            items = [m for m in items if m.movement_type == movement_type]
        return items[offset : offset + limit], len(items)

    async def get_forecast(self, inventory_id, *, window_days=30, lead_time_days=None):
        await self.get(inventory_id)
        if self.forecast_override is not None:
            return self.forecast_override
        return StockoutForecast(
            has_sufficient_data=False, daily_run_rate=0.0, confidence_score=0.0
        )


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


async def _create_product(client, **overrides):
    payload = {"business_profile_id": str(uuid.uuid4()), "item_name": "Handwoven Scarf"}
    payload.update(overrides)
    response = await client.post(BASE_URL, json=payload)
    return response


async def test_create_returns_201_with_created_product(client, fake_service):
    business_profile_id = str(uuid.uuid4())

    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "item_name": "Handwoven Scarf",
            "current_quantity": 10,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["item_name"] == "Handwoven Scarf"
    assert body["current_quantity"] == 10
    assert body["business_profile_id"] == business_profile_id


async def test_create_invalid_payload_returns_422(client, fake_service):
    response = await _create_product(client, item_name="")
    assert response.status_code == 422


async def test_create_conflict_returns_409(client, fake_service):
    fake_service.raise_on_create = InventoryConflictError(
        "sku is already in use by another product for this business."
    )
    response = await _create_product(client)
    assert response.status_code == 409


async def test_create_invalid_reference_returns_422(client, fake_service):
    fake_service.raise_on_create = InvalidReferenceError(
        "business_profile_id does not reference an existing business profile."
    )
    response = await _create_product(client)
    assert response.status_code == 422


async def test_get_missing_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_get_existing_returns_200(client, fake_service):
    create_resp = await _create_product(client)
    product_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{product_id}")

    assert response.status_code == 200
    assert response.json()["item_name"] == "Handwoven Scarf"


async def test_list_without_business_profile_id_returns_422(client, fake_service):
    response = await client.get(BASE_URL)
    assert response.status_code == 422


async def test_list_filters_by_category(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await _create_product(
        client, business_profile_id=business_profile_id, category="Textiles"
    )
    await _create_product(
        client,
        business_profile_id=business_profile_id,
        item_name="Bracelet",
        category="Jewelry",
    )

    response = await client.get(
        BASE_URL,
        params={"business_profile_id": business_profile_id, "category": "Textiles"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["category"] == "Textiles"


async def test_list_search_via_q_param(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await _create_product(client, business_profile_id=business_profile_id)
    await _create_product(
        client, business_profile_id=business_profile_id, item_name="Clay Pot"
    )

    response = await client.get(
        BASE_URL, params={"business_profile_id": business_profile_id, "q": "scarf"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["item_name"] == "Handwoven Scarf"


async def test_update_applies_partial_fields(client, fake_service):
    create_resp = await _create_product(client, category="Textiles")
    product_id = create_resp.json()["id"]

    response = await client.patch(
        f"{BASE_URL}/{product_id}", json={"item_name": "Renamed Scarf"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["item_name"] == "Renamed Scarf"
    assert body["category"] == "Textiles"


async def test_update_rejects_current_quantity_field(client, fake_service):
    create_resp = await _create_product(client)
    product_id = create_resp.json()["id"]

    response = await client.patch(
        f"{BASE_URL}/{product_id}", json={"current_quantity": 999}
    )

    assert response.status_code == 422


async def test_update_missing_returns_404(client, fake_service):
    response = await client.patch(f"{BASE_URL}/{uuid.uuid4()}", json={"item_name": "X"})
    assert response.status_code == 404


async def test_delete_returns_204_and_deactivates(client, fake_service):
    create_resp = await _create_product(client)
    product_id = create_resp.json()["id"]

    response = await client.delete(f"{BASE_URL}/{product_id}")

    assert response.status_code == 204
    assert fake_service.store[uuid.UUID(product_id)].is_active is False


async def test_delete_missing_returns_404(client, fake_service):
    response = await client.delete(f"{BASE_URL}/{uuid.uuid4()}")
    assert response.status_code == 404


# -- stock operations -------------------------------------------------------


async def test_stock_in_increases_quantity(client, fake_service):
    create_resp = await _create_product(client, current_quantity=10)
    product_id = create_resp.json()["id"]

    response = await client.post(
        f"{BASE_URL}/{product_id}/stock-in", json={"quantity": 5}
    )

    assert response.status_code == 200
    assert response.json()["current_quantity"] == 15


async def test_stock_in_rejects_non_positive_quantity(client, fake_service):
    create_resp = await _create_product(client)
    product_id = create_resp.json()["id"]

    response = await client.post(
        f"{BASE_URL}/{product_id}/stock-in", json={"quantity": 0}
    )

    assert response.status_code == 422


async def test_stock_out_decreases_quantity(client, fake_service):
    create_resp = await _create_product(client, current_quantity=10)
    product_id = create_resp.json()["id"]

    response = await client.post(
        f"{BASE_URL}/{product_id}/stock-out", json={"quantity": 4}
    )

    assert response.status_code == 200
    assert response.json()["current_quantity"] == 6


async def test_stock_out_insufficient_stock_returns_409(client, fake_service):
    fake_service.raise_on_stock_out = InsufficientStockError(
        "Cannot remove 4 units: only 3 in stock."
    )
    create_resp = await _create_product(client, current_quantity=3)
    product_id = create_resp.json()["id"]

    response = await client.post(
        f"{BASE_URL}/{product_id}/stock-out", json={"quantity": 4}
    )

    assert response.status_code == 409


async def test_adjust_stock_sets_absolute_quantity(client, fake_service):
    create_resp = await _create_product(client, current_quantity=10)
    product_id = create_resp.json()["id"]

    response = await client.post(
        f"{BASE_URL}/{product_id}/adjust", json={"new_quantity": 7, "notes": "Recount"}
    )

    assert response.status_code == 200
    assert response.json()["current_quantity"] == 7


async def test_movements_history_returns_recorded_entries(client, fake_service):
    create_resp = await _create_product(client, current_quantity=10)
    product_id = create_resp.json()["id"]
    await client.post(f"{BASE_URL}/{product_id}/stock-in", json={"quantity": 5})
    await client.post(f"{BASE_URL}/{product_id}/stock-out", json={"quantity": 2})

    response = await client.get(f"{BASE_URL}/{product_id}/movements")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {m["movement_type"] for m in body["items"]} == {"restock", "sale"}


async def test_movements_missing_product_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}/movements")
    assert response.status_code == 404


# -- low-stock / out-of-stock / summary route-ordering ------------------------


async def test_low_stock_route_does_not_collide_with_get_by_id(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await _create_product(
        client,
        business_profile_id=business_profile_id,
        current_quantity=2,
        reorder_level=5,
    )

    response = await client.get(
        f"{BASE_URL}/low-stock", params={"business_profile_id": business_profile_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1


async def test_out_of_stock_route_does_not_collide_with_get_by_id(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await _create_product(
        client, business_profile_id=business_profile_id, current_quantity=0
    )

    response = await client.get(
        f"{BASE_URL}/out-of-stock", params={"business_profile_id": business_profile_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1


async def test_summary_route_does_not_collide_with_get_by_id(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await _create_product(
        client,
        business_profile_id=business_profile_id,
        current_quantity=10,
        unit_cost=2,
    )

    response = await client.get(
        f"{BASE_URL}/summary", params={"business_profile_id": business_profile_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_products"] == 1
    assert body["total_stock_value"] == 20.0


# -- forecast (app.ai.forecasting.stockout) ---------------------------------


async def test_forecast_missing_product_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}/forecast")
    assert response.status_code == 404


async def test_forecast_insufficient_data_reports_false(client, fake_service):
    create_resp = await _create_product(client, current_quantity=10)
    product_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{product_id}/forecast")

    assert response.status_code == 200
    body = response.json()
    assert body["has_sufficient_data"] is False
    assert body["projected_stockout_date"] is None


async def test_forecast_returns_projected_dates_when_available(client, fake_service):
    create_resp = await _create_product(client, current_quantity=10)
    product_id = create_resp.json()["id"]
    fake_service.forecast_override = StockoutForecast(
        has_sufficient_data=True,
        daily_run_rate=2.0,
        days_of_stock_remaining=5.0,
        projected_stockout_date="2026-08-10",
        reorder_by_date="2026-08-05",
        confidence_score=80.0,
    )

    response = await client.get(f"{BASE_URL}/{product_id}/forecast")

    assert response.status_code == 200
    body = response.json()
    assert body["has_sufficient_data"] is True
    assert body["days_of_stock_remaining"] == 5.0
    assert body["projected_stockout_date"] == "2026-08-10"
    assert body["reorder_by_date"] == "2026-08-05"


async def test_openapi_schema_documents_inventory_routes(client, fake_service):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/low-stock" in paths
    assert f"{BASE_URL}/out-of-stock" in paths
    assert f"{BASE_URL}/summary" in paths
    assert f"{BASE_URL}/{{inventory_id}}" in paths
    assert f"{BASE_URL}/{{inventory_id}}/stock-in" in paths
    assert f"{BASE_URL}/{{inventory_id}}/stock-out" in paths
    assert f"{BASE_URL}/{{inventory_id}}/adjust" in paths
    assert f"{BASE_URL}/{{inventory_id}}/movements" in paths
    assert f"{BASE_URL}/{{inventory_id}}/forecast" in paths
    assert set(paths[BASE_URL]) >= {"post", "get"}
    assert set(paths[f"{BASE_URL}/{{inventory_id}}"]) >= {"get", "patch", "delete"}
