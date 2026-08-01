"""Data-access layer for inventory_movements (the append-only stock ledger).

Builds entirely on BaseRepository for create/get_by_id/get_all/exists/
count — movements are append-only, so update()/delete() are inherited but
never called by InventoryService (see that service). The additions here
are list_by_inventory (newest-first, matching
idx_inventory_movements_inventory) and search() over notes.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import InventoryMovementType
from app.models.inventory_movement import InventoryMovement
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("notes",)


class InventoryMovementRepository(BaseRepository[InventoryMovement]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, InventoryMovement)

    async def list_by_inventory(
        self,
        inventory_id: uuid.UUID,
        *,
        movement_type: InventoryMovementType | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[InventoryMovement], int]:
        filters: dict[str, object] = {"inventory_id": inventory_id}
        if movement_type is not None:
            filters["movement_type"] = movement_type
        return await self.get_all(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=InventoryMovement.movement_date.desc(),
        )

    async def search(
        self,
        query: str,
        *,
        inventory_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[InventoryMovement], int]:
        """Substring search over movement notes, optionally narrowed to
        one item's history."""
        filters = {"inventory_id": inventory_id} if inventory_id is not None else None
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
