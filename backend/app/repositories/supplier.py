"""Data-access layer for suppliers.

Builds entirely on BaseRepository for create/get_by_id/get_all/update/
delete/exists — the only additions are list_by_business_profile and
search(). No Supplier schemas/service/router exist yet — this repository
exists so Inventory can integrate with real supplier data (e.g. "filter by
supplier") without inventing a duplicate data-access path; a full Supplier
CRUD module is a separate task, not implied by completing Inventory.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("name", "contact_person", "category", "email")


class SupplierRepository(BaseRepository[Supplier]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Supplier)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Supplier], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if is_active is not None:
            filters["is_active"] = is_active
        return await self.get_all(filters=filters, limit=limit, offset=offset)

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Supplier], int]:
        """Substring search over name/contact_person/category/email,
        optionally narrowed to one business's suppliers."""
        filters = (
            {"business_profile_id": business_profile_id}
            if business_profile_id is not None
            else None
        )
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
