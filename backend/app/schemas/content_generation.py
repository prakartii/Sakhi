"""Request/response schemas for POST /content-calendar/generate."""

import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.schemas.content_calendar_item import ContentCalendarItemRead


class ContentCalendarGenerateRequest(BaseModel):
    business_profile_id: uuid.UUID
    month: date = Field(description="Any date within the target month.")
    platforms: list[str] = Field(default_factory=lambda: ["instagram", "facebook"])
    posts_per_week: int = Field(default=3, ge=1, le=7)


class ContentCalendarGenerateResponse(BaseModel):
    items: list[ContentCalendarItemRead]
