"""Pydantic v2 request/response schemas for Marketing Studio.

`analysis`/`reel_brief` reuse app.ai.marketing.models.ContentAnalysis/
ReelBrief directly rather than re-declaring mirror classes here — a
deliberate, narrow exception to this codebase's usual "schemas layer stays
separate from AI output shapes" convention (see e.g. app/schemas/
analytics_summary.py for the normal pattern). Those two AI models were
already designed as pure I/O shapes with zero ORM coupling — nothing about
them is specific to the LLM call that produces them — so a mirror class
here would be a verbatim duplicate with no behavioral difference, not a
real abstraction boundary.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.ai.marketing.models import ContentAnalysis, ContentMetrics, ReelBrief
from app.models.enums import MarketingAnalysisSourceType


class MarketingAnalysisOut(BaseModel):
    id: uuid.UUID
    business_profile_id: uuid.UUID
    social_connection_id: uuid.UUID | None
    source_type: MarketingAnalysisSourceType
    source_url: str | None
    caption: str | None
    hashtags: list[str]
    comments_sample: list[str]
    metrics: ContentMetrics
    engagement_rate: float | None
    analysis: ContentAnalysis | None
    reel_brief: ReelBrief | None
    created_at: datetime
    updated_at: datetime


class MarketingAnalysisListResponse(BaseModel):
    items: list[MarketingAnalysisOut]
    total: int
    limit: int
    offset: int


class GenerateReelBriefRequest(BaseModel):
    business_profile_id: uuid.UUID
    angle: str | None = Field(
        default=None,
        max_length=300,
        description="Optional steer for the idea, e.g. 'something for Diwali' or "
        "'show the packaging process'. Left blank, Sakhi picks what best fits the business.",
    )
