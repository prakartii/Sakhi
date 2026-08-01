"""Unit tests for InventoryService. Both repositories and the DB session
are faked/mocked — no database connection is used or required.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import InventoryMovementType
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    StockAdjustmentRequest,
    StockInRequest,
    StockOutRequest,
)
from app.services.inventory import (
    InsufficientStockError,
    InventoryConflictError,
    InventoryNotFoundError,
    InventoryService,
    InvalidReferenceError,
)


class _FakeInventoryRepository:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, Inventory] = {}
        self.raise_on_write: Exception | None = None

    async def create(self, item: Inventory) -> Inventory:
        if self.raise_on_write:
            raise self.raise_on_write
        item.id = item.id or uuid.uuid4()
        self.store[item.id] = item
        return item

    async def get_by_id(self, inventory_id: uuid.UUID) -> Inventory | None:
        return self.store.get(inventory_id)

    async def update(self, item: Inventory, data: dict) -> Inventory:
        if self.raise_on_write:
            raise self.raise_on_write
        for field, value in data.items():
            setattr(item, field, value)
        return item

    async def deactivate(self, item: Inventory) -> Inventory:
        item.is_active = False
        return item

    async def list_by_business_profile(
        self,
        business_profile_id,
        *,
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
        if category is not None:
            items = [i for i in items if i.category == category]
        if supplier_id is not None:
            items = [i for i in items if i.supplier_id == supplier_id]
        if is_active is not None:
            items = [i for i in items if i.is_active == is_active]
        return items[offset : offset + limit], len(items)

    async def search(
        self,
        query,
        *,
        business_profile_id=None,
        category=None,
        supplier_id=None,
        is_active=None,
        limit=20,
        offset=0,
    ):
        items = [
            i
            for i in self.store.values()
            if query.lower() in i.item_name.lower()
            and (
                business_profile_id is None
                or i.business_profile_id == business_profile_id
            )
        ]
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
            "total_products": len(items),
            "total_stock_value": sum(
                i.current_quantity * (i.unit_cost or 0) for i in items
            ),
            "low_stock_count": sum(
                1 for i in items if 0 < i.current_quantity <= i.reorder_level
            ),
            "out_of_stock_count": sum(1 for i in items if i.current_quantity <= 0),
        }


class _FakeMovementRepository:
    def __init__(self) -> None:
        self.store: list[InventoryMovement] = []
        self.raise_on_write: Exception | None = None

    async def create(self, movement: InventoryMovement) -> InventoryMovement:
        if self.raise_on_write:
            raise self.raise_on_write
        movement.id = movement.id or uuid.uuid4()
        self.store.append(movement)
        return movement

    async def list_by_inventory(
        self, inventory_id, *, movement_type=None, limit=20, offset=0
    ):
        # Newest-first, approximated by reversing insertion order — real
        # created_at/movement_date are only populated by the database
        # (server_default), never set on these fake in-memory objects.
        items = [m for m in reversed(self.store) if m.inventory_id == inventory_id]
        if movement_type is not None:
            items = [m for m in items if m.movement_type == movement_type]
        return items[offset : offset + limit], len(items)


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _make_service():
    repo = _FakeInventoryRepository()
    movement_repo = _FakeMovementRepository()
    session = AsyncMock()
    service = InventoryService(
        session, repository=repo, movement_repository=movement_repo
    )
    return service, repo, movement_repo, session


def _create_payload(**overrides) -> InventoryCreate:
    data = {"business_profile_id": uuid.uuid4(), "item_name": "Handwoven Scarf"}
    data.update(overrides)
    return InventoryCreate(**data)


# -- create ---------------------------------------------------------------


async def test_create_persists_and_commits():
    service, repo, _movements, session = _make_service()

    result = await service.create(_create_payload())

    assert result.item_name == "Handwoven Scarf"
    assert result.id in repo.store
    session.commit.assert_awaited_once()


async def test_create_with_initial_stock_records_a_movement():
    service, _repo, movements, _session = _make_service()

    item = await service.create(_create_payload(current_quantity=25))

    assert len(movements.store) == 1
    assert movements.store[0].movement_type == InventoryMovementType.ADJUSTMENT
    assert movements.store[0].quantity_before == 0
    assert movements.store[0].quantity_after == 25
    assert movements.store[0].notes == "Initial stock"
    assert movements.store[0].inventory_id == item.id


async def test_create_with_zero_stock_records_no_movement():
    service, _repo, movements, _session = _make_service()

    await service.create(_create_payload())

    assert movements.store == []


async def test_create_translates_sku_conflict():
    service, repo, _movements, session = _make_service()
    repo.raise_on_write = _integrity_error(
        'duplicate key value violates unique constraint "uq_inventory_business_sku"'
    )

    with pytest.raises(InventoryConflictError):
        await service.create(_create_payload(sku="ABC-1"))
    session.rollback.assert_awaited_once()


async def test_create_translates_invalid_business_profile_reference():
    service, repo, _movements, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "inventory" violates foreign key '
        'constraint "inventory_business_profile_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload())


async def test_create_translates_invalid_supplier_reference():
    service, repo, _movements, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "inventory" violates foreign key '
        'constraint "inventory_supplier_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload(supplier_id=uuid.uuid4()))


async def test_create_reraises_unrecognized_integrity_error():
    service, repo, _movements, _session = _make_service()
    repo.raise_on_write = _integrity_error("some_other_constraint_violation")

    with pytest.raises(IntegrityError):
        await service.create(_create_payload())


# -- get / list -------------------------------------------------------------


async def test_get_missing_raises_not_found():
    service, _repo, _movements, _session = _make_service()

    with pytest.raises(InventoryNotFoundError):
        await service.get(uuid.uuid4())


async def test_list_filters_by_category_and_supplier():
    service, _repo, _movements, _session = _make_service()
    business_profile_id = uuid.uuid4()
    supplier_id = uuid.uuid4()
    await service.create(
        _create_payload(business_profile_id=business_profile_id, category="Textiles")
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            item_name="Bracelet",
            category="Jewelry",
            supplier_id=supplier_id,
        )
    )

    textiles, textiles_total = await service.list(
        business_profile_id, category="Textiles"
    )
    by_supplier, supplier_total = await service.list(
        business_profile_id, supplier_id=supplier_id
    )

    assert textiles_total == 1
    assert textiles[0].category == "Textiles"
    assert supplier_total == 1
    assert by_supplier[0].item_name == "Bracelet"


async def test_list_with_q_delegates_to_search():
    service, _repo, _movements, _session = _make_service()
    business_profile_id = uuid.uuid4()
    await service.create(_create_payload(business_profile_id=business_profile_id))
    await service.create(
        _create_payload(business_profile_id=business_profile_id, item_name="Clay Pot")
    )

    items, total = await service.list(business_profile_id, q="scarf")

    assert total == 1
    assert items[0].item_name == "Handwoven Scarf"


# -- update / delete ----------------------------------------------------------


async def test_update_applies_only_provided_fields():
    service, _repo, _movements, session = _make_service()
    created = await service.create(_create_payload(category="Textiles"))

    updated = await service.update(created.id, InventoryUpdate(item_name="Renamed"))

    assert updated.item_name == "Renamed"
    assert updated.category == "Textiles"  # untouched
    session.commit.assert_awaited()


async def test_update_missing_raises_not_found():
    service, _repo, _movements, _session = _make_service()

    with pytest.raises(InventoryNotFoundError):
        await service.update(uuid.uuid4(), InventoryUpdate(item_name="X"))


async def test_delete_deactivates_instead_of_removing():
    service, repo, _movements, session = _make_service()
    created = await service.create(_create_payload())

    await service.delete(created.id)

    assert repo.store[created.id].is_active is False
    assert created.id in repo.store  # still present — not hard-deleted
    session.commit.assert_awaited()


async def test_delete_missing_raises_not_found():
    service, _repo, _movements, _session = _make_service()

    with pytest.raises(InventoryNotFoundError):
        await service.delete(uuid.uuid4())


# -- stock operations -------------------------------------------------------


async def test_stock_in_increases_quantity_and_records_restock():
    service, _repo, movements, session = _make_service()
    created = await service.create(_create_payload(current_quantity=10))

    updated = await service.stock_in(
        created.id, StockInRequest(quantity=5, notes="Delivery")
    )

    assert updated.current_quantity == 15
    restock = [
        m for m in movements.store if m.movement_type == InventoryMovementType.RESTOCK
    ]
    assert len(restock) == 1
    assert restock[0].quantity == 5
    assert restock[0].quantity_before == 10
    assert restock[0].quantity_after == 15
    session.commit.assert_awaited()


async def test_stock_in_missing_item_raises_not_found():
    service, _repo, _movements, _session = _make_service()

    with pytest.raises(InventoryNotFoundError):
        await service.stock_in(uuid.uuid4(), StockInRequest(quantity=1))


async def test_stock_out_decreases_quantity_and_records_sale():
    service, _repo, movements, session = _make_service()
    created = await service.create(_create_payload(current_quantity=10))

    updated = await service.stock_out(created.id, StockOutRequest(quantity=4))

    assert updated.current_quantity == 6
    sale = [m for m in movements.store if m.movement_type == InventoryMovementType.SALE]
    assert len(sale) == 1
    assert sale[0].quantity_before == 10
    assert sale[0].quantity_after == 6
    session.commit.assert_awaited()


async def test_stock_out_to_exactly_zero_succeeds():
    service, _repo, _movements, _session = _make_service()
    created = await service.create(_create_payload(current_quantity=5))

    updated = await service.stock_out(created.id, StockOutRequest(quantity=5))

    assert updated.current_quantity == 0


async def test_stock_out_rejects_quantity_exceeding_stock():
    service, repo, movements, session = _make_service()
    created = await service.create(_create_payload(current_quantity=3))
    movement_count_before = len(
        movements.store
    )  # create() already logged "Initial stock"
    session.commit.reset_mock()

    with pytest.raises(InsufficientStockError):
        await service.stock_out(created.id, StockOutRequest(quantity=4))

    # Nothing changed and nothing new was recorded/committed for the
    # rejected attempt.
    assert repo.store[created.id].current_quantity == 3
    assert len(movements.store) == movement_count_before
    session.commit.assert_not_awaited()


async def test_stock_out_missing_item_raises_not_found():
    service, _repo, _movements, _session = _make_service()

    with pytest.raises(InventoryNotFoundError):
        await service.stock_out(uuid.uuid4(), StockOutRequest(quantity=1))


async def test_adjust_stock_sets_absolute_quantity_and_records_adjustment():
    service, _repo, movements, session = _make_service()
    created = await service.create(_create_payload(current_quantity=10))

    updated = await service.adjust_stock(
        created.id, StockAdjustmentRequest(new_quantity=7, notes="Physical count")
    )

    assert updated.current_quantity == 7
    adjustments = [
        m
        for m in movements.store
        if m.movement_type == InventoryMovementType.ADJUSTMENT
    ]
    # One from create's initial-stock snapshot, one from this adjustment.
    assert len(adjustments) == 2
    latest = adjustments[-1]
    assert latest.quantity_before == 10
    assert latest.quantity_after == 7
    assert latest.quantity == 3
    assert latest.notes == "Physical count"
    session.commit.assert_awaited()


async def test_adjust_stock_missing_item_raises_not_found():
    service, _repo, _movements, _session = _make_service()

    with pytest.raises(InventoryNotFoundError):
        await service.adjust_stock(uuid.uuid4(), StockAdjustmentRequest(new_quantity=1))


async def test_list_movements_returns_history_newest_first():
    service, _repo, _movements, _session = _make_service()
    created = await service.create(_create_payload(current_quantity=10))
    await service.stock_in(created.id, StockInRequest(quantity=5))
    await service.stock_out(created.id, StockOutRequest(quantity=2))

    items, total = await service.list_movements(created.id)

    assert total == 3  # initial stock + stock_in + stock_out
    assert {m.movement_type for m in items} == {
        InventoryMovementType.ADJUSTMENT,
        InventoryMovementType.RESTOCK,
        InventoryMovementType.SALE,
    }


async def test_list_movements_missing_item_raises_not_found():
    service, _repo, _movements, _session = _make_service()

    with pytest.raises(InventoryNotFoundError):
        await service.list_movements(uuid.uuid4())


# -- low stock / out of stock / summary ---------------------------------------


async def test_list_low_stock_and_out_of_stock_delegate_to_repository():
    service, _repo, _movements, _session = _make_service()
    business_profile_id = uuid.uuid4()
    low = await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            item_name="Low Item",
            current_quantity=2,
            reorder_level=5,
        )
    )
    out = await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            item_name="Out Item",
            current_quantity=0,
        )
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            item_name="Healthy Item",
            current_quantity=50,
            reorder_level=5,
        )
    )

    low_items, low_total = await service.list_low_stock(business_profile_id)
    out_items, out_total = await service.list_out_of_stock(business_profile_id)

    assert low_total == 1
    assert low_items[0].id == low.id
    assert out_total == 1
    assert out_items[0].id == out.id


async def test_get_summary_aggregates_expected_fields():
    service, _repo, _movements, _session = _make_service()
    business_profile_id = uuid.uuid4()
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            current_quantity=10,
            unit_cost=2.5,
        )
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            item_name="Out Item",
            current_quantity=0,
        )
    )

    summary = await service.get_summary(business_profile_id)

    assert summary["business_profile_id"] == business_profile_id
    assert summary["total_products"] == 2
    assert summary["total_stock_value"] == 25.0
    assert summary["out_of_stock_count"] == 1
