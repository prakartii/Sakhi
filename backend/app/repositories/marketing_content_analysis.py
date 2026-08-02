"""Data-access layer for marketing_content_analyses (Marketing Studio's
analysis history — Sakhi's business-intelligence record of what's already
been analyzed for a business)."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketing_content_analysis import MarketingContentAnalysis
from app.repositories.base import BaseRepository


class MarketingContentAnalysisRepository(BaseRepository[MarketingContentAnalysis]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MarketingContentAnalysis)

    async def list_by_business_profile(
        self,
        business_profile_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MarketingContentAnalysis], int]:
        return await self.get_all(
            filters={"business_profile_id": business_profile_id},
            limit=limit,
            offset=offset,
        )
