"""Data-access layer for inventory (Smart Inventory current-state stock).

Builds on BaseRepository for create/get_by_id/get_all/update/exists — the
additions here are list_by_business_profile (now covering category/
supplier/active filters), search() (same filters plus free text),
list_low_stock/list_out_of_stock (comparison-based queries the generic
equality-filter dict in BaseRepository can't express), get_summary (a
single aggregate query), and deactivate (the mechanical column-set
operation InventoryService uses instead of delete() — see that service
for why).
"""

import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory
from app.repositories.base import BaseRepository, RepositoryError

_SEARCH_FIELDS = ("item_name", "sku", "category")


class InventoryRepository(BaseRepository[Inventory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Inventory)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        category: str | None = None,
        supplier_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Inventory], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if category is not None:
            filters["category"] = category
        if supplier_id is not None:
            filters["supplier_id"] = supplier_id
        if is_active is not None:
            filters["is_active"] = is_active
        return await self.get_all(
            filters=filters, limit=limit, offset=offset, order_by=Inventory.item_name
        )

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        category: str | None = None,
        supplier_id: uuid.UUID | None = None,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Inventory], int]:
        """Substring search over item_name/sku/category, optionally
        narrowed by business/category/supplier/active — the same filters
        list_by_business_profile supports, so a client can search and
        filter in one call."""
        filters: dict[str, object] = {}
        if business_profile_id is not None:
            filters["business_profile_id"] = business_profile_id
        if category is not None:
            filters["category"] = category
        if supplier_id is not None:
            filters["supplier_id"] = supplier_id
        if is_active is not None:
            filters["is_active"] = is_active
        return await self._search(
            query,
            fields=_SEARCH_FIELDS,
            filters=filters or None,
            limit=limit,
            offset=offset,
        )

    async def list_low_stock(
        self,
        business_profile_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Inventory], int]:
        """Active items with stock at or below reorder level but not yet
        at zero — "running low," distinct from list_out_of_stock. Needs a
        column-to-column comparison (current_quantity <= reorder_level),
        which the generic equality-filter dict can't express."""
        self._validate_pagination(limit, offset)
        condition = and_(
            Inventory.business_profile_id == business_profile_id,
            Inventory.is_active.is_(True),
            Inventory.current_quantity > 0,
            Inventory.current_quantity <= Inventory.reorder_level,
        )
        return await self._list_by_condition(condition, limit=limit, offset=offset)

    async def list_out_of_stock(
        self,
        business_profile_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Inventory], int]:
        """Active items with zero (or, defensively, negative) stock."""
        self._validate_pagination(limit, offset)
        condition = and_(
            Inventory.business_profile_id == business_profile_id,
            Inventory.is_active.is_(True),
            Inventory.current_quantity <= 0,
        )
        return await self._list_by_condition(condition, limit=limit, offset=offset)

    async def get_summary(self, business_profile_id: uuid.UUID) -> dict[str, object]:
        """One aggregate query for the business's active inventory:
        product count, stock value at cost, and low/out-of-stock counts —
        deliberately computed in the database rather than by fetching
        every row and summing in Python."""
        stmt = select(
            func.count().label("total_products"),
            func.coalesce(
                func.sum(
                    Inventory.current_quantity * func.coalesce(Inventory.unit_cost, 0)
                ),
                0,
            ).label("total_stock_value"),
            func.count()
            .filter(
                Inventory.current_quantity > 0,
                Inventory.current_quantity <= Inventory.reorder_level,
            )
            .label("low_stock_count"),
            func.count()
            .filter(Inventory.current_quantity <= 0)
            .label("out_of_stock_count"),
        ).where(
            Inventory.business_profile_id == business_profile_id,
            Inventory.is_active.is_(True),
        )
        try:
            row = (await self.session.execute(stmt)).one()
        except SQLAlchemyError as exc:
            raise RepositoryError(
                f"Failed to summarize inventory for business_profile_id={business_profile_id!r}"
            ) from exc
        return {
            "total_products": row.total_products,
            "total_stock_value": float(row.total_stock_value),
            "low_stock_count": row.low_stock_count,
            "out_of_stock_count": row.out_of_stock_count,
        }

    async def deactivate(self, item: Inventory) -> Inventory:
        item.is_active = False
        await self.session.flush()
        return item

    async def _list_by_condition(
        self, condition, *, limit: int, offset: int
    ) -> tuple[list[Inventory], int]:
        count_stmt = select(func.count()).select_from(Inventory).where(condition)
        list_stmt = (
            select(Inventory)
            .where(condition)
            .order_by(Inventory.current_quantity.asc())
            .limit(limit)
            .offset(offset)
        )
        try:
            total = (await self.session.execute(count_stmt)).scalar_one()
            rows = (await self.session.execute(list_stmt)).scalars().all()
        except SQLAlchemyError as exc:
            raise RepositoryError("Failed to list inventory by stock status") from exc
        return list(rows), total
