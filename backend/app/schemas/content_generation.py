"""Request/response schemas for POST /content-calendar/generate and
POST /content-calendar/{item_id}/regenerate."""

import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.ai.content.models import CampaignFocus
from app.schemas.content_calendar_item import ContentCalendarItemRead


class ContentCalendarGenerateRequest(BaseModel):
    business_profile_id: uuid.UUID
    month: date = Field(description="Any date within the target month.")
    platforms: list[str] = Field(default_factory=lambda: ["instagram", "facebook"])
    posts_per_week: int = Field(default=3, ge=1, le=7)
    campaign_focus: CampaignFocus = Field(
        default="general",
        description="Themes the whole month's copy: a festival/seasonal push, "
        "a product launch, a promotional offer, or a bundle idea.",
    )
    campaign_note: str | None = Field(
        default=None,
        max_length=500,
        description="Specifics for the campaign focus, e.g. which product is "
        "launching, or what the offer/bundle is. Ignored when campaign_focus "
        "is 'general'.",
    )


class ContentCalendarGenerateResponse(BaseModel):
    items: list[ContentCalendarItemRead]


class ContentRegenerateRequest(BaseModel):
    instructions: str | None = Field(
        default=None,
        max_length=500,
        description="Optional free-text rewrite request, e.g. 'make it shorter' "
        "or 'lean into the festival more'. Date/platform/type stay fixed.",
    )
