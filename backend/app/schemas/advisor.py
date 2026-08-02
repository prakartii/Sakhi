"""Pydantic v2 request/response schemas for the AI Advisor chat.

Grounded conversational Q&A over app.ai.orchestrator — see
app/api/v1/endpoints/advisor.py for how a message becomes an answer.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AdvisorChatRequest(BaseModel):
    business_profile_id: uuid.UUID
    message: str = Field(..., min_length=1, max_length=2000)


class AdvisorChatResponse(BaseModel):
    answer: str
    used_services: list[str]
    sources: list[str]


class AdvisorChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime


class AdvisorChatHistoryResponse(BaseModel):
    messages: list[AdvisorChatMessageOut]
