"""Pydantic v2 request/response schemas for the Content Calendar module.

Kept separate from app.models.content_calendar_item (the ORM shape) on
purpose, same as every other module in this codebase: format/shape
validation lives here at the API boundary. Whether a social_connection_id
actually belongs to the same business (and the same platform) requires
interpreting data, not just its shape — that lives in
ContentCalendarItemService instead.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ContentStatus, ContentType, SocialMediaPlatform

_BLANK_TO_NONE_FIELDS = ("caption", "image_prompt", "call_to_action")


class ContentCalendarItemBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=200)]
    content_type: ContentType
    platform: SocialMediaPlatform
    social_connection_id: UUID | None = Field(
        default=None,
        description="An existing, connected social account for this "
        "platform. Optional — content can be planned before an account is "
        "connected.",
    )
    caption: Annotated[str | None, Field(max_length=5000)] = None
    # No per-item min_length here: blank/whitespace-only entries are
    # dropped by _normalize_hashtags below rather than rejected outright,
    # so a stray blank in the list doesn't fail the whole request.
    hashtags: list[Annotated[str, Field(max_length=100)]] | None = None
    image_prompt: Annotated[str | None, Field(max_length=2000)] = None
    generated_image_url: str | None = None
    generated_video_url: str | None = None
    call_to_action: Annotated[str | None, Field(max_length=200)] = None
    scheduled_datetime: datetime | None = None
    status: ContentStatus = ContentStatus.DRAFT
    ai_generated: bool = False

    @field_validator("title")
    @classmethod
    def _reject_blank_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("title cannot be blank")
        return value

    @field_validator(*_BLANK_TO_NONE_FIELDS)
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        return value or None

    @field_validator("hashtags")
    @classmethod
    def _normalize_hashtags(cls, value: list[str] | None) -> list[str] | None:
        """Trims each tag and prefixes a leading '#' if the caller omitted
        it, e.g. "handmade" and "#handmade" both normalize to "#handmade".
        Empty entries (blank strings) are dropped; an all-blank list
        normalizes to None rather than an empty list."""
        if value is None:
            return None
        normalized: list[str] = []
        for tag in value:
            tag = tag.strip()
            if not tag:
                continue
            normalized.append(tag if tag.startswith("#") else f"#{tag}")
        return normalized or None


class ContentCalendarItemCreate(ContentCalendarItemBase):
    business_profile_id: UUID = Field(
        description="The business this content item belongs to."
    )


class ContentCalendarItemUpdate(ContentCalendarItemBase):
    """PATCH semantics: only fields explicitly present in the request body
    are applied (see ContentCalendarItemService.update, which calls
    model_dump(exclude_unset=True)) — omitting a field leaves it untouched.
    `title`/`content_type`/`platform` are the only three fields Base
    requires with no default, so they're the only three overridden as
    optional here; every other field already tolerates omission via its
    own default. `status`/`ai_generated` keep Base's non-nullable typing,
    so an explicit `null` is rejected with a 422 instead of failing as a
    database constraint error.
    """

    title: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    content_type: ContentType | None = None
    platform: SocialMediaPlatform | None = None


class ContentCalendarItemRead(ContentCalendarItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_profile_id: UUID
    created_at: datetime
    updated_at: datetime


class ContentCalendarItemListResponse(BaseModel):
    items: list[ContentCalendarItemRead]
    total: int
    limit: int
    offset: int
