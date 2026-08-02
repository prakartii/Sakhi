"""Pydantic v2 request/response schemas for Website Management.

Kept separate from app.models.website(_version) (the ORM shape) on purpose,
same as every other module in this codebase: format/shape validation
(domain shape, URL scheme, non-blank website_name) lives here at the API
boundary. The one genuinely interpretive rule in this module — assigning
each new snapshot the next version_number for its website — belongs in the
service layer instead; see WebsiteService.
"""

import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import WebsiteStatus

_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
_DOMAIN_PATTERN = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")

_BLANK_TO_NONE_FIELDS = (
    "github_repository",
    "template",
    "seo_title",
    "seo_description",
)


class WebsiteBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    website_name: Annotated[str, Field(min_length=1, max_length=200)]
    deployment_url: Annotated[str | None, Field(max_length=2048)] = None
    github_repository: Annotated[str | None, Field(max_length=300)] = None
    template: Annotated[str | None, Field(max_length=100)] = None
    status: WebsiteStatus = WebsiteStatus.DRAFT
    seo_title: Annotated[str | None, Field(max_length=200)] = None
    seo_description: Annotated[str | None, Field(max_length=300)] = None
    custom_domain: Annotated[str | None, Field(max_length=255)] = None
    favicon: Annotated[str | None, Field(max_length=2048)] = None
    published: bool = False
    preview_slug: Annotated[str | None, Field(max_length=80)] = None

    @field_validator("website_name")
    @classmethod
    def _reject_blank_website_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("website_name cannot be blank")
        return value

    @field_validator(*_BLANK_TO_NONE_FIELDS)
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        # str_strip_whitespace already trimmed it; an all-whitespace input is
        # now "" here, which is more useful to callers as "not provided".
        return value or None

    @field_validator("deployment_url", "favicon")
    @classmethod
    def _validate_url_scheme(cls, value: str | None) -> str | None:
        if value is not None and not _URL_PATTERN.match(value):
            raise ValueError("must be a valid URL starting with http:// or https://")
        return value

    @field_validator("custom_domain")
    @classmethod
    def _validate_domain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.lower()  # domains are case-insensitive; the DB uniqueness
        # constraint is a plain case-sensitive index, so normalizing here is what
        # actually makes "Example.com" and "example.com" collide as intended.
        if not value:
            return None
        if not _DOMAIN_PATTERN.match(value):
            raise ValueError(
                "custom_domain must be a bare domain, e.g. 'shop.example.com' "
                "(no scheme, no path)"
            )
        return value


class WebsiteCreate(WebsiteBase):
    business_profile_id: UUID = Field(
        description="The business this website belongs to."
    )


class WebsiteUpdate(WebsiteBase):
    """PATCH semantics: only fields explicitly present in the request body
    are applied (see WebsiteService.update, which calls
    model_dump(exclude_unset=True)) — omitting a field leaves it untouched.
    `status` keeps Base's non-nullable typing, so an explicit `null` is
    rejected with a 422 instead of failing as a database constraint error.

    `change_notes` is not a website column — it's carried through to the
    version snapshot this update produces (see WebsiteService.update) and
    then discarded from the write applied to the website row itself.
    """

    website_name: Annotated[str, Field(min_length=1, max_length=200)] | None = None
    change_notes: Annotated[str | None, Field(max_length=1000)] = None


class WebsiteRead(WebsiteBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_profile_id: UUID
    # AI-authored, not settable via WebsiteCreate/WebsiteUpdate — see
    # WebsiteService.update_content(), the only writer of these two.
    content: dict | None = None
    images: dict | None = None
    created_at: datetime
    updated_at: datetime


class WebsiteListResponse(BaseModel):
    items: list[WebsiteRead]
    total: int
    limit: int
    offset: int


class WebsiteVersionRead(BaseModel):
    """A single immutable snapshot from a website's version history."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    website_id: UUID
    version_number: int
    website_name: str
    deployment_url: str | None
    github_repository: str | None
    template: str | None
    status: WebsiteStatus
    seo_title: str | None
    seo_description: str | None
    custom_domain: str | None
    favicon: str | None
    published: bool
    change_notes: str | None
    content: dict | None = None
    images: dict | None = None
    created_at: datetime
    updated_at: datetime


class WebsiteVersionListResponse(BaseModel):
    items: list[WebsiteVersionRead]
    total: int
    limit: int
    offset: int
