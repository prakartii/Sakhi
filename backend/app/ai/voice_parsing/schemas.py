"""Pydantic schemas for structured voice-transcript parsing output.

Field names and constraints mirror the `business_memory` / `voice_logs`
columns in supabase/migrations (06_voice_logs, 07_business_memory_and_embeddings)
so a parsed result can be persisted with no field remapping.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

MemoryType = Literal["fact", "milestone", "goal", "challenge", "preference", "note", "decision"]
Sentiment = Literal["positive", "neutral", "negative", "mixed"]


class ParsedMemoryItem(BaseModel):
    """One business-memory candidate extracted from a transcript. Maps
    directly onto a business_memory row (source='voice')."""

    memory_type: MemoryType
    title: str | None = Field(default=None, max_length=200)
    content: str
    importance_score: int = Field(ge=1, le=5)
    occurred_at: str | None = Field(
        default=None,
        description="ISO 8601 date/datetime if the speaker referenced a resolvable time, else null.",
    )


class ParsedVoiceLog(BaseModel):
    """Full structured result for one voice check-in transcript. `sentiment`
    maps onto voice_logs.sentiment; each entry in `memories` becomes a
    candidate business_memory row."""

    sentiment: Sentiment
    memories: list[ParsedMemoryItem] = Field(default_factory=list)
