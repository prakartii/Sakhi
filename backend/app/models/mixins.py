"""Reusable declarative mixins matching the conventions already established
in the Supabase schema (see supabase/migrations): UUID primary keys and
created_at/updated_at timestamps on every table.

Concrete models compose these instead of redeclaring the same three columns
on every class, e.g.:

    class BusinessProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
        __tablename__ = "business_profiles"
        ...
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
