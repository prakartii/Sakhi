"""Data-access layer for conversation_history (turn-by-turn AI conversation log)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_history import ConversationHistory
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("content",)


class ConversationHistoryRepository(BaseRepository[ConversationHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ConversationHistory)

    async def list_by_session(
        self,
        session_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ConversationHistory], int]:
        """Oldest-first — matches idx_conversation_history_session, so a
        thread replays in the order it happened."""
        return await self.get_all(
            filters={"session_id": session_id},
            limit=limit,
            offset=offset,
            order_by=ConversationHistory.created_at,
        )

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ConversationHistory], int]:
        return await self.get_all(
            filters={"business_profile_id": business_profile_id},
            limit=limit,
            offset=offset,
            order_by=ConversationHistory.created_at.desc(),
        )

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ConversationHistory], int]:
        """Substring search over message content, optionally narrowed to
        one business's conversation history."""
        filters = (
            {"business_profile_id": business_profile_id}
            if business_profile_id is not None
            else None
        )
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
