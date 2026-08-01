"""Pydantic v2 request/response schemas for the Business Profile module.

Kept separate from app.models.business_profile (the ORM shape) on purpose:
these describe the API contract and carry format validation (GSTIN/PAN/PIN
code patterns, URL shape) that has no place on the storage model. Format/
shape validation like that lives here at the API boundary by long-standing
FastAPI convention; genuinely interpretive business rules — e.g. what
"onboarding complete" means — live in the service layer instead (see
BusinessProfileService.get_onboarding_status), not here and not in the
repository.
"""

import re
from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import BusinessRegistrationType, BusinessStage, BusinessStatus

_GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
_PAN_PATTERN = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
_PINCODE_PATTERN = re.compile(r"^[1-9][0-9]{5}$")
_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
_CURRENT_YEAR = date.today().year


def _clean_upper(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip().upper()
    return value or None


class BusinessProfileBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    business_name: Annotated[str, Field(min_length=1, max_length=200)]
    business_category: Annotated[str | None, Field(max_length=100)] = None
    industry: Annotated[str | None, Field(max_length=100)] = None
    registration_type: BusinessRegistrationType = BusinessRegistrationType.UNREGISTERED
    gstin: Annotated[str | None, Field(max_length=15)] = None
    pan: Annotated[str | None, Field(max_length=10)] = None
    udyam_registration_number: Annotated[str | None, Field(max_length=30)] = None
    year_established: Annotated[int | None, Field(ge=1900, le=_CURRENT_YEAR)] = None
    employee_count_range: Annotated[str | None, Field(max_length=20)] = None
    monthly_revenue_range: Annotated[str | None, Field(max_length=30)] = None
    preferred_language_id: UUID | None = None
    city: Annotated[str | None, Field(max_length=100)] = None
    state: Annotated[str | None, Field(max_length=100)] = None
    country: Annotated[str, Field(min_length=1, max_length=100)] = "India"
    pincode: Annotated[str | None, Field(max_length=10)] = None
    address: Annotated[str | None, Field(max_length=1000)] = None
    logo_url: Annotated[str | None, Field(max_length=2048)] = None
    is_primary: bool = True
    status: BusinessStatus = BusinessStatus.ACTIVE

    # -- onboarding / growth-workflow fields --------------------------------
    owner_name: Annotated[str | None, Field(max_length=200)] = None
    business_description: Annotated[str | None, Field(max_length=2000)] = None
    target_audience: Annotated[str | None, Field(max_length=1000)] = None
    products_or_services: Annotated[str | None, Field(max_length=2000)] = None
    business_stage: BusinessStage | None = None
    website_url: Annotated[str | None, Field(max_length=2048)] = None
    instagram_url: Annotated[str | None, Field(max_length=2048)] = None
    facebook_url: Annotated[str | None, Field(max_length=2048)] = None
    linkedin_url: Annotated[str | None, Field(max_length=2048)] = None

    @field_validator("business_name")
    @classmethod
    def _reject_blank_business_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not value.strip():
            raise ValueError("business_name cannot be blank")
        return value

    @field_validator("gstin")
    @classmethod
    def _validate_gstin(cls, value: str | None) -> str | None:
        value = _clean_upper(value)
        if value is not None and not _GSTIN_PATTERN.match(value):
            raise ValueError(
                "gstin must be a valid 15-character GSTIN, e.g. 27AAAPL1234C1Z5"
            )
        return value

    @field_validator("pan")
    @classmethod
    def _validate_pan(cls, value: str | None) -> str | None:
        value = _clean_upper(value)
        if value is not None and not _PAN_PATTERN.match(value):
            raise ValueError("pan must be a valid 10-character PAN, e.g. ABCDE1234F")
        return value

    @field_validator("pincode")
    @classmethod
    def _validate_pincode(cls, value: str | None) -> str | None:
        if value is not None and not _PINCODE_PATTERN.match(value):
            raise ValueError("pincode must be a valid 6-digit Indian PIN code")
        return value

    @field_validator(
        "owner_name", "business_description", "target_audience", "products_or_services"
    )
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        # str_strip_whitespace already trimmed it; an all-whitespace input is
        # now "" here, which is more useful to callers as "not provided".
        return value or None

    @field_validator("website_url", "instagram_url", "facebook_url", "linkedin_url")
    @classmethod
    def _validate_url_scheme(cls, value: str | None) -> str | None:
        if value is not None and not _URL_PATTERN.match(value):
            raise ValueError("must be a valid URL starting with http:// or https://")
        return value


class BusinessProfileCreate(BusinessProfileBase):
    user_id: UUID = Field(
        description="Owning user id. Supplied explicitly for now — "
        "there is no session/auth to derive it from yet."
    )


class BusinessProfileUpdate(BusinessProfileBase):
    """PATCH semantics: only fields explicitly present in the request body
    are applied (see BusinessProfileService.update, which calls
    model_dump(exclude_unset=True)) — omitting a field leaves it untouched
    regardless of the default shown below, Base's per-field validators
    (GSTIN/PAN/PIN code format, non-blank business_name, URL shape) still
    apply, and NOT NULL columns (registration_type, country, is_primary,
    status) keep Base's non-nullable typing so an explicit `null` is
    rejected with a 422 instead of failing as a database constraint error.
    The onboarding fields added in this schema are all nullable in the
    database, so `null` is a legitimate way to clear one of them.
    """

    business_name: Annotated[str, Field(min_length=1, max_length=200)] | None = None


class BusinessProfilePut(BusinessProfileBase):
    """PUT (full-replace) semantics: the caller sends the complete
    representation of the profile. Any field omitted from the request body
    is reset to the default shown above (None for optional fields, the
    listed default for registration_type/country/is_primary/status) rather
    than left untouched — that's what distinguishes PUT from PATCH here.
    Structurally identical to BusinessProfileBase; named separately purely
    so it shows up as its own schema in the generated OpenAPI docs.
    """


class BusinessProfileRead(BusinessProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class BusinessProfileListResponse(BaseModel):
    items: list[BusinessProfileRead]
    total: int
    limit: int
    offset: int


class BusinessProfileOnboardingStatus(BaseModel):
    """Response for GET .../onboarding-status. See
    BusinessProfileService.get_onboarding_status for what counts as
    required vs. optional — that decision lives in the service, not here.
    """

    business_profile_id: UUID
    is_complete: bool
    completion_percentage: Annotated[float, Field(ge=0, le=100)]
    completed_fields: list[str]
    missing_fields: list[str]
