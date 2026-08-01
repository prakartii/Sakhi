"""Pydantic v2 request/response schemas for the Notification module.

Kept separate from app.models.notification (the ORM shape) on purpose, same
as every other module in this codebase — see app/schemas/transaction.py for
the pattern this follows.

Two field-name notes, both resolved against the *existing* `notifications`
table/model (unchanged, per this task's constraints) rather than by adding
columns:

  * The request-shape concept of a notification "message" is this table's
    existing `body` column — schemas use `body` to stay 1:1 with the real
    column, matching every other module's convention.
  * There is no `status` column. Read state is tracked by `is_read` +
    `read_at`. NotificationRead exposes a derived `status` ("unread"/"read")
    for API ergonomics, and list-filtering accepts a `status` query param
    that the service translates into an `is_read` filter.

`channel` (in_app/email/sms/push/whatsapp) is a real column but is
deliberately not exposed on NotificationCreate: this module only implements
in-app notifications (no email/push delivery), so every notification is
created with channel=in_app regardless of what a caller might request —
offering the other values here would imply delivery this module doesn't
perform. It's still visible on NotificationRead for transparency.
"""

import re
import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.models.enums import NotificationChannel, NotificationPriority, NotificationType

NotificationStatus = Literal["unread", "read"]

_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

_BLANK_TO_NONE_FIELDS = ("body", "related_entity_type")


class NotificationBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    notification_type: NotificationType
    title: Annotated[str, Field(min_length=1, max_length=200)]
    body: Annotated[str | None, Field(max_length=5000)] = None
    action_url: Annotated[str | None, Field(max_length=2048)] = None
    related_entity_type: Annotated[str | None, Field(max_length=50)] = None
    related_entity_id: uuid.UUID | None = None
    priority: NotificationPriority = NotificationPriority.NORMAL

    @field_validator(*_BLANK_TO_NONE_FIELDS)
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        return value or None

    @field_validator("action_url")
    @classmethod
    def _validate_url_scheme(cls, value: str | None) -> str | None:
        if value is not None and not _URL_PATTERN.match(value):
            raise ValueError("must be a valid URL starting with http:// or https://")
        return value


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID = Field(
        description="Recipient user (temporary — explicit until auth exists, "
        "same gap already documented on every other module's *_id fields)."
    )
    business_profile_id: uuid.UUID | None = Field(
        default=None,
        description="Business this notification relates to. Omit for "
        "account-level notifications (e.g. system announcements) that "
        "aren't tied to a specific business.",
    )


class NotificationRead(NotificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    business_profile_id: uuid.UUID | None
    channel: NotificationChannel
    is_read: bool
    read_at: datetime | None
    sent_at: datetime | None
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def status(self) -> NotificationStatus:
        return "read" if self.is_read else "unread"


class NotificationListResponse(BaseModel):
    items: list[NotificationRead]
    total: int
    limit: int
    offset: int


class MarkAllReadResponse(BaseModel):
    updated_count: int
