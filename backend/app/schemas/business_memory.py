"""Pydantic v2 response schemas for the Business Memory module.

Read-only: every business_memory row is written by the voice pipeline (see
app.services.voice.VoiceConversationService) or a future AI-inferred writer,
never directly by a client, so this module only exposes listing/reading —
no Create/Update schema, matching how the module is actually populated.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import MemorySource, MemoryType


class BusinessMemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_profile_id: uuid.UUID
    source_voice_log_id: uuid.UUID | None
    memory_type: MemoryType
    title: str | None
    content: str
    source: MemorySource
    importance_score: int
    is_archived: bool
    occurred_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BusinessMemoryListResponse(BaseModel):
    items: list[BusinessMemoryRead]
    total: int
    limit: int
    offset: int


class MemorySearchResultOut(BaseModel):
    business_memory_id: uuid.UUID
    title: str | None
    content: str
    similarity: float


class MemorySearchResponse(BaseModel):
    query: str
    results: list[MemorySearchResultOut]


class MemoryInsightsResponse(BaseModel):
    """A narrated 'Why' over a business's memory stats (app.ai.explanations),
    grounded in facts computed from the business's own memory rows."""

    why: str
    basis: str
    total: int
    top_type: str | None
    avg_importance: float | None
