"""Data-access layer for voice_logs (Voice Check-ins recordings/transcripts)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import VoiceLogStatus
from app.models.voice_log import VoiceLog
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("transcript",)


class VoiceLogRepository(BaseRepository[VoiceLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VoiceLog)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        status: VoiceLogStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[VoiceLog], int]:
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if status is not None:
            filters["status"] = status
        return await self.get_all(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=VoiceLog.recorded_at.desc(),
        )

    async def search(
        self,
        query: str,
        *,
        business_profile_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[VoiceLog], int]:
        """Substring search over transcript text, optionally narrowed to
        one business's recordings. Rows with a NULL transcript (not yet
        transcribed) never match — ILIKE against NULL is NULL, which SQL
        treats as false in a WHERE clause, so no special-casing is needed."""
        filters = (
            {"business_profile_id": business_profile_id}
            if business_profile_id is not None
            else None
        )
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
