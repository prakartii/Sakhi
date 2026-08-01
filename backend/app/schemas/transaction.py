"""Pydantic v2 request/response schemas for the Finance module (Transaction).

Kept separate from app.models.transaction (the ORM shape) on purpose, same
as every other module in this codebase: format/shape validation (URL
scheme, non-negative amount, blank-text normalization) lives here at the
API boundary. Rules that require interpreting a value rather than just its
shape — a supplier_id that doesn't exist, an is_recurring transaction with
no frequency — belong in the service layer instead; see TransactionService.
"""

import re
from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    PaymentMethod,
    RecurringFrequency,
    TransactionSource,
    TransactionStatus,
    TransactionType,
)

_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

_BLANK_TO_NONE_FIELDS = (
    "category",
    "counterparty_name",
    "counterparty_contact",
    "description",
)


class TransactionBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    transaction_type: TransactionType
    category: Annotated[str | None, Field(max_length=100)] = None
    amount: Annotated[float, Field(ge=0)]
    currency: Annotated[str, Field(min_length=1, max_length=10)] = "INR"
    payment_method: PaymentMethod = PaymentMethod.CASH
    counterparty_name: Annotated[str | None, Field(max_length=200)] = None
    counterparty_contact: Annotated[str | None, Field(max_length=50)] = None
    transaction_date: date = Field(default_factory=date.today)
    description: Annotated[str | None, Field(max_length=1000)] = None
    receipt_url: Annotated[str | None, Field(max_length=2048)] = None
    is_recurring: bool = False
    recurring_frequency: RecurringFrequency | None = None
    status: TransactionStatus = TransactionStatus.COMPLETED
    source: TransactionSource = TransactionSource.MANUAL
    supplier_id: UUID | None = None

    @field_validator("currency")
    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("currency cannot be blank")
        return value

    @field_validator(*_BLANK_TO_NONE_FIELDS)
    @classmethod
    def _blank_optional_text_to_none(cls, value: str | None) -> str | None:
        # str_strip_whitespace already trimmed it; an all-whitespace input is
        # now "" here, which is more useful to callers as "not provided".
        return value or None

    @field_validator("receipt_url")
    @classmethod
    def _validate_url_scheme(cls, value: str | None) -> str | None:
        if value is not None and not _URL_PATTERN.match(value):
            raise ValueError("must be a valid URL starting with http:// or https://")
        return value


class TransactionCreate(TransactionBase):
    business_profile_id: UUID = Field(
        description="The business this transaction belongs to."
    )


class TransactionUpdate(TransactionBase):
    """PATCH semantics: only fields explicitly present in the request body
    are applied (see TransactionService.update, which calls
    model_dump(exclude_unset=True)) — omitting a field leaves it untouched.
    `transaction_type` and `amount` are the only two fields Base requires
    with no default, so they're the only two overridden as optional here;
    every other field already tolerates omission via its own default.
    """

    transaction_type: TransactionType | None = None
    amount: Annotated[float, Field(ge=0)] | None = None


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    business_profile_id: UUID
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int
