"""Pydantic v2 request/response schemas for Social Media Connections.

Kept separate from app.models.social_media_connection (the ORM shape) on
purpose, same as every other module in this codebase. One deliberate
departure from that "schema mirrors the model" convention: access_token and
refresh_token are real columns but never appear on
SocialMediaConnectionRead. Returning stored secrets in an API response is a
security bug waiting to happen regardless of how carefully routers are
written, so the safer contract is enforced at the schema itself — a router
that returns SocialMediaConnectionRead cannot leak a token even if it
tried. Connect/RefreshToken accept tokens as write-only input; nothing in
this module echoes one back.
"""

import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import SocialConnectionStatus, SocialMediaPlatform

_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

_BLANK_TO_NONE_FIELDS = ("account_name", "account_id")


class _ProfileUrlValidatorMixin(BaseModel):
    @field_validator("profile_url", check_fields=False)
    @classmethod
    def _validate_url_scheme(cls, value: str | None) -> str | None:
        if value is not None and not _URL_PATTERN.match(value):
            raise ValueError("must be a valid URL starting with http:// or https://")
        return value


class SocialMediaConnectionCreate(_ProfileUrlValidatorMixin):
    """Payload for "Connect Account". access_token is the only required
    token field — some providers never issue a refresh token, and
    token_expiry is unknown for providers that issue non-expiring tokens."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    business_profile_id: UUID = Field(
        description="The business connecting this platform account."
    )
    platform: SocialMediaPlatform
    account_name: Annotated[str | None, Field(max_length=200)] = None
    account_id: Annotated[str | None, Field(max_length=200)] = None
    profile_url: Annotated[str | None, Field(max_length=2048)] = None
    access_token: Annotated[str, Field(min_length=1)]
    refresh_token: Annotated[str | None, Field(min_length=1)] = None
    token_expiry: datetime | None = None

    @field_validator(*_BLANK_TO_NONE_FIELDS)
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        return value or None


class RefreshTokenRequest(BaseModel):
    """Payload for "Refresh Token". This module never talks to a platform
    API — the caller (a future OAuth-handling module, or a manual
    operation) has already obtained a new token elsewhere; this just
    records it."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    access_token: Annotated[str, Field(min_length=1)]
    refresh_token: Annotated[str | None, Field(min_length=1)] = None
    token_expiry: datetime | None = None


class SyncMetadataRequest(_ProfileUrlValidatorMixin):
    """Payload for "Sync Metadata". Same non-calling caveat as
    RefreshTokenRequest: the caller supplies whatever it already fetched
    from the platform; this just persists it and stamps last_sync."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    account_name: Annotated[str | None, Field(max_length=200)] = None
    account_id: Annotated[str | None, Field(max_length=200)] = None
    profile_url: Annotated[str | None, Field(max_length=2048)] = None

    @field_validator(*_BLANK_TO_NONE_FIELDS)
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        return value or None


class SocialMediaConnectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)

    id: UUID
    business_profile_id: UUID
    platform: SocialMediaPlatform
    account_name: str | None
    account_id: str | None
    profile_url: str | None
    token_expiry: datetime | None
    connection_status: SocialConnectionStatus
    last_sync: datetime | None
    created_at: datetime
    updated_at: datetime


class SocialMediaConnectionListResponse(BaseModel):
    items: list[SocialMediaConnectionRead]
    total: int
    limit: int
    offset: int
