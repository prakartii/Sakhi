"""Request/response schemas for POST /voice/converse and POST /voice/transcribe."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MemoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    memory_type: str
    title: str | None
    content: str
    importance_score: int
    occurred_at: datetime | None


class VoiceConverseResponse(BaseModel):
    voice_log_id: uuid.UUID
    session_id: uuid.UUID
    transcript: str
    detected_language: str | None
    sentiment: str
    memories: list[MemoryOut]
    answer: str
    used_services: list[str]
    sources: list[str]
    audio_base64: str | None
    audio_format: str


class TranscribeResponse(BaseModel):
    transcript: str
    detected_language: str | None
    confidence: float | None
