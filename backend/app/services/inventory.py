"""Business logic for the Inventory module.

Owns the transaction boundary (commit/rollback) around each use case and
translates database-level failures into domain exceptions the API layer
maps to HTTP status codes — routers never see SQLAlchemy exceptions
directly. Format/shape validation (non-negative prices, URL scheme) lives
in the Pydantic schemas at the API boundary. What belongs here instead,
because it requires interpreting the data rather than just its shape:

  * translating a foreign-key/uniqueness violation into which reference or
    SKU is the problem;
  * "stock cannot become negative" on stock_out — a rule about the
    relationship between two numbers, not either number's shape alone;
  * keeping inventory_movements a true audit trail: every quantity change
    (create with a starting count, stock_in, stock_out, adjust_stock)
    writes a movement row in the same transaction as the quantity change,
    so `current_quantity` is never edited without a record of why.
"""

from __future__ import annotations
# ^ Load-bearing, not stylistic: this class has a method literally named
# `list`. Once that `def list(...)` binds in the class namespace, any
# LATER method (list_low_stock, list_out_of_stock, list_movements) that
# writes a bare `list[...]` in its own return annotation would otherwise
# resolve `list` to that method instead of the builtin, and blow up with
# "'function' object is not subscriptable" the moment the module is
# imported. Deferred/string annotations sidestep the whole class of bug.
# See app/services/website.py for the same technique used for the same
# reason.

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.enums import InventoryMovementType
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.repositories.inventory import InventoryRepository
from app.repositories.inventory_movement import InventoryMovementRepository
from app.schemas.inventory import (
    InventoryCreate,
    InventoryUpdate,
    StockAdjustmentRequest,
    StockInRequest,
    StockOutRequest,
)

logger = get_logger(__name__)


class InventoryNotFoundError(Exception):
    """No inventory row exists for the given id."""


class InvalidReferenceError(Exception):
    """A referenced business_profile_id, supplier_id, or
    related_transaction_id does not exist."""


class InventoryConflictError(Exception):
    """The write violates a uniqueness rule — sku already used by another
    product for this business (uq_inventory_business_sku)."""


class InsufficientStockError(Exception):
    """A stock_out (or adjustment) would make current_quantity negative."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "uq_inventory_business_sku" in message:
        return InventoryConflictError(
            "sku is already in use by another product for this business."
        )
    if "inventory_business_profile_id_fkey" in message:
        return InvalidReferenceError(
            "business_profile_id does not reference an existing business profile."
        )
    if "inventory_supplier_id_fkey" in message:
        return InvalidReferenceError(
            "supplier_id does not reference an existing supplier."
        )
    if "inventory_movements_related_transaction_id_fkey" in message:
        return InvalidReferenceError(
            "related_transaction_id does not reference an existing transaction."
        )
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500.
    return exc


class InventoryService:
    def __init__(
        self,
        session: AsyncSession,
        repository: InventoryRepository | None = None,
        movement_repository: InventoryMovementRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or InventoryRepository(session)
        self._movement_repo = movement_repository or InventoryMovementRepository(
            session
        )

    # -- product CRUD ---------------------------------------------------------

    async def create(self, payload: InventoryCreate) -> Inventory:
        item = Inventory(**payload.model_dump())
        try:
            await self._repo.create(item)
            if item.current_quantity > 0:
                await self._record_movement(
                    item,
                    movement_type=InventoryMovementType.ADJUSTMENT,
                    quantity_before=0,
                    quantity_after=item.current_quantity,
                    notes="Initial stock",
                )
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        logger.info(
            "inventory.create item_id=%s business_profile_id=%s quantity=%s",
            item.id,
            item.business_profile_id,
            item.current_quantity,
        )
        return item

    async def get(self, inventory_id: uuid.UUID) -> Inventory:
        item = await self._repo.get_by_id(inventory_id)
        if item is None:
            raise InventoryNotFoundError(str(inventory_id))
        return item

    async def list(
        self,
        business_profile_id: uuid.UUID,
        *,
        q: str | None = None,
        category: str | None = None,
        supplier_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Inventory], int]:
        """Lists (or, if `q` is given, searches) a business's products,
        optionally narrowed by category/supplier/active-status — every
        filter applies whether or not `q` is present."""
        if q:
            return await self._repo.search(
                q,
                business_profile_id=business_profile_id,
                category=category,
                supplier_id=supplier_id,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )
        return await self._repo.list_by_business_profile(
            business_profile_id,
            category=category,
            supplier_id=supplier_id,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

    async def list_low_stock(
        self, business_profile_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[Inventory], int]:
        return await self._repo.list_low_stock(
            business_profile_id, limit=limit, offset=offset
        )

    async def list_out_of_stock(
        self, business_profile_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[Inventory], int]:
        return await self._repo.list_out_of_stock(
            business_profile_id, limit=limit, offset=offset
        )

    async def get_summary(self, business_profile_id: uuid.UUID) -> dict[str, object]:
        summary = await self._repo.get_summary(business_profile_id)
        return {"business_profile_id": business_profile_id, **summary}

    async def update(
        self, inventory_id: uuid.UUID, payload: InventoryUpdate
    ) -> Inventory:
        """PATCH: applies only the fields the caller actually supplied.
        current_quantity is never one of them — see InventoryUpdate."""
        item = await self.get(inventory_id)
        data = payload.model_dump(exclude_unset=True)
        try:
            await self._repo.update(item, data)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return item

    async def delete(self, inventory_id: uuid.UUID) -> None:
        """Deactivates (is_active=False) rather than hard-deleting.
        inventory_movements.inventory_id is ON DELETE CASCADE — a real
        DELETE here would silently erase the exact audit trail this
        service exists to maintain. transaction_items.inventory_id is
        nullable (ON DELETE SET NULL) so it wouldn't even block a hard
        delete at the database level, which makes deactivation a
        deliberate choice, not one forced by a constraint.
        """
        item = await self.get(inventory_id)
        await self._repo.deactivate(item)
        await self._session.commit()
        logger.info("inventory.deactivate item_id=%s", item.id)

    # -- stock operations -------------------------------------------------

    async def stock_in(
        self, inventory_id: uuid.UUID, payload: StockInRequest
    ) -> Inventory:
        item = await self.get(inventory_id)
        quantity_before = item.current_quantity
        quantity_after = quantity_before + payload.quantity
        try:
            await self._repo.update(item, {"current_quantity": quantity_after})
            await self._record_movement(
                item,
                movement_type=InventoryMovementType.RESTOCK,
                quantity=payload.quantity,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                notes=payload.notes,
                related_transaction_id=payload.related_transaction_id,
            )
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        logger.info(
            "inventory.stock_in item_id=%s quantity=%s before=%s after=%s",
            item.id,
            payload.quantity,
            quantity_before,
            quantity_after,
        )
        return item

    async def stock_out(
        self, inventory_id: uuid.UUID, payload: StockOutRequest
    ) -> Inventory:
        item = await self.get(inventory_id)
        quantity_before = item.current_quantity
        quantity_after = quantity_before - payload.quantity
        if quantity_after < 0:
            logger.warning(
                "inventory.stock_out rejected item_id=%s requested=%s available=%s",
                item.id,
                payload.quantity,
                quantity_before,
            )
            raise InsufficientStockError(
                f"Cannot remove {payload.quantity} units: only {quantity_before} in stock."
            )
        try:
            await self._repo.update(item, {"current_quantity": quantity_after})
            await self._record_movement(
                item,
                movement_type=InventoryMovementType.SALE,
                quantity=payload.quantity,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                notes=payload.notes,
                related_transaction_id=payload.related_transaction_id,
            )
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        logger.info(
            "inventory.stock_out item_id=%s quantity=%s before=%s after=%s",
            item.id,
            payload.quantity,
            quantity_before,
            quantity_after,
        )
        return item

    async def adjust_stock(
        self, inventory_id: uuid.UUID, payload: StockAdjustmentRequest
    ) -> Inventory:
        """Sets stock to an absolute value (e.g. after a physical count),
        as opposed to stock_in/stock_out's relative +/- quantity."""
        item = await self.get(inventory_id)
        quantity_before = item.current_quantity
        quantity_after = payload.new_quantity
        await self._repo.update(item, {"current_quantity": quantity_after})
        await self._record_movement(
            item,
            movement_type=InventoryMovementType.ADJUSTMENT,
            quantity=abs(quantity_after - quantity_before),
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            notes=payload.notes,
        )
        await self._session.commit()
        logger.info(
            "inventory.adjust_stock item_id=%s before=%s after=%s",
            item.id,
            quantity_before,
            quantity_after,
        )
        return item

    async def list_movements(
        self,
        inventory_id: uuid.UUID,
        *,
        movement_type: InventoryMovementType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[InventoryMovement], int]:
        await self.get(inventory_id)  # 404s cleanly if the item itself is missing
        return await self._movement_repo.list_by_inventory(
            inventory_id, movement_type=movement_type, limit=limit, offset=offset
        )

    async def _record_movement(
        self,
        item: Inventory,
        *,
        movement_type: InventoryMovementType,
        quantity_before: float,
        quantity_after: float,
        quantity: float | None = None,
        notes: str | None = None,
        related_transaction_id: uuid.UUID | None = None,
    ) -> InventoryMovement:
        movement = InventoryMovement(
            inventory_id=item.id,
            related_transaction_id=related_transaction_id,
            movement_type=movement_type,
            quantity=quantity
            if quantity is not None
            else abs(quantity_after - quantity_before),
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            notes=notes,
        )
        await self._movement_repo.create(movement)
        return movement
