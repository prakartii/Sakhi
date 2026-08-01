"""Data-access layer for transactions (the Cashflow Health ledger)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("description", "counterparty_name", "category")


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Transaction)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        transaction_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if transaction_type is not None:
            filters["transaction_type"] = transaction_type
        if status is not None:
            filters["status"] = status
        return await self.get_all(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=Transaction.transaction_date.desc(),
        )

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        """Substring search over description/counterparty_name/category,
        optionally narrowed to one business's transactions."""
        filters = (
            {"business_profile_id": business_profile_id}
            if business_profile_id is not None
            else None
        )
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
