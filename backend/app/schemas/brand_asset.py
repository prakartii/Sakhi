"""Pydantic v2 request/response schemas for Brand Assets.

Kept separate from app.models.brand_asset (the ORM shape) on purpose, same
as every other module in this codebase: format/shape validation (hex color,
URL scheme, non-blank brand_name) lives here at the API boundary. Anything
that requires interpreting a value rather than just checking its shape
belongs in the service layer instead — see BrandAssetService.
"""

import re
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import BrandAssetStatus

_HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9A-Fa-f]{3}){1,2}$")
_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

_BLANK_TO_NONE_FIELDS = (
    "tagline",
    "brand_story",
    "mission",
    "vision",
    "typography",
    "brand_voice",
    "packaging_notes",
)


class BrandAssetBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    brand_name: Annotated[str, Field(min_length=1, max_length=200)]
    tagline: Annotated[str | None, Field(max_length=300)] = None
    brand_story: Annotated[str | None, Field(max_length=5000)] = None
    mission: Annotated[str | None, Field(max_length=2000)] = None
    vision: Annotated[str | None, Field(max_length=2000)] = None
    primary_color: Annotated[str | None, Field(max_length=7)] = None
    secondary_color: Annotated[str | None, Field(max_length=7)] = None
    typography: Annotated[str | None, Field(max_length=200)] = None
    logo_url: Annotated[str | None, Field(max_length=2048)] = None
    favicon_url: Annotated[str | None, Field(max_length=2048)] = None
    brand_voice: Annotated[str | None, Field(max_length=1000)] = None
    packaging_notes: Annotated[str | None, Field(max_length=2000)] = None
    status: BrandAssetStatus = BrandAssetStatus.DRAFT

    @field_validator("brand_name")
    @classmethod
    def _reject_blank_brand_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("brand_name cannot be blank")
        return value

    @field_validator(*_BLANK_TO_NONE_FIELDS)
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        # str_strip_whitespace already trimmed it; an all-whitespace input is
        # now "" here, which is more useful to callers as "not provided".
        return value or None

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _validate_hex_color(cls, value: str | None) -> str | None:
        if value is not None and not _HEX_COLOR_PATTERN.match(value):
            raise ValueError("must be a hex color like #8F2F56 or #FFF")
        return value

    @field_validator("logo_url", "favicon_url")
    @classmethod
    def _validate_url_scheme(cls, value: str | None) -> str | None:
        if value is not None and not _URL_PATTERN.match(value):
            raise ValueError("must be a valid URL starting with http:// or https://")
        return value


class BrandAssetCreate(BrandAssetBase):
    business_profile_id: UUID = Field(
        description="The business this brand identity belongs to."
    )


class BrandAssetUpdate(BrandAssetBase):
    """PATCH semantics: only fields explicitly present in the request body
    are applied (see BrandAssetService.update, which calls
    model_dump(exclude_unset=True)) — omitting a field leaves it untouched.
    `status` keeps Base's non-nullable typing, so an explicit `null` is
    rejected with a 422 instead of failing as a database constraint error.
    """

    brand_name: Annotated[str, Field(min_length=1, max_length=200)] | None = None


class BrandAssetRead(BrandAssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_profile_id: UUID
    created_at: datetime
    updated_at: datetime


class BrandAssetListResponse(BaseModel):
    items: list[BrandAssetRead]
    total: int
    limit: int
    offset: int
