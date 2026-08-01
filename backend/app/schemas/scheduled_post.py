"""Pydantic v2 request/response schemas for Scheduled Posts.

Kept separate from app.models.scheduled_post (the ORM shape) on purpose,
same as every other module in this codebase. Whether content_calendar_id/
social_connection_id actually reference the right business/platform, and
whether a status transition is allowed, both require interpreting data —
that lives in ScheduledPostService, not here.

There is deliberately no generic "update" schema: this module only
implements the five named operations (Schedule Post, Cancel Schedule,
Retry Failed Post, Update Status, plus the Get Queue/Publishing History
reads) — not an open-ended PATCH of every column. UpdateStatusRequest is
the one write schema for reporting an outcome, matching the "record data
obtained elsewhere, don't call the API yourself" pattern already
established by RefreshTokenRequest/SyncMetadataRequest in the Social Media
Connections module.
"""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PublishingStatus

_BLANK_TO_NONE_FIELDS = ("published_url", "error_log")


class ScheduledPostCreate(BaseModel):
    """Payload for "Schedule Post". No publishing_status/retry_count/
    published_url/etc here — every scheduled post starts `queued` with a
    clean outcome slate; those fields are only ever set by Update Status,
    Cancel Schedule, or Retry Failed Post."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    business_profile_id: UUID = Field(
        description="The business this scheduled post belongs to."
    )
    content_calendar_id: UUID = Field(
        description="The content_calendar_items row being scheduled."
    )
    social_connection_id: UUID = Field(
        description="The connected social account to publish through."
    )
    scheduled_time: datetime = Field(
        description="When this post should go out. Must be in the future."
    )

    @field_validator("scheduled_time")
    @classmethod
    def _assume_utc_when_naive(cls, value: datetime) -> datetime:
        """A caller that sends an offset-less timestamp almost certainly
        means UTC (the column is timestamptz) rather than the server's
        local time — attaching UTC here keeps the "must be in the future"
        check in the service from comparing naive vs. aware datetimes."""
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


class UpdateStatusRequest(BaseModel):
    """Payload for "Update Status" — records the outcome of a publish
    attempt made elsewhere. This module never calls a platform API; a
    future publishing worker reports back through this endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    publishing_status: PublishingStatus
    published_url: Annotated[str | None, Field(max_length=2048)] = None
    provider_response: dict | None = Field(
        default=None,
        description="Opaque JSON captured from the platform API by the "
        "caller — stored as-is, never interpreted here.",
    )
    error_log: Annotated[str | None, Field(max_length=5000)] = None

    @field_validator(*_BLANK_TO_NONE_FIELDS)
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        return value or None


class ScheduledPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_profile_id: UUID
    content_calendar_id: UUID
    social_connection_id: UUID
    scheduled_time: datetime
    publishing_status: PublishingStatus
    retry_count: int
    published_url: str | None
    provider_response: dict | None
    error_log: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ScheduledPostListResponse(BaseModel):
    items: list[ScheduledPostRead]
    total: int
    limit: int
    offset: int
