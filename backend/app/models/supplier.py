"""ORM mapping for public.suppliers.

Maps 1:1 onto supabase/migrations/20260801100009_suppliers.sql.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.inventory import Inventory
    from app.models.transaction import Transaction


class Supplier(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "suppliers"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        CheckConstraint(
            "rating is null or rating between 0 and 5", name="chk_suppliers_rating"
        ),
    )

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(100))
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="suppliers"
    )
    inventory_items: Mapped[list["Inventory"]] = relationship(back_populates="supplier")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="supplier")


Index("idx_suppliers_business_profile", Supplier.business_profile_id)
Index(
    "idx_suppliers_active",
    Supplier.business_profile_id,
    postgresql_where=(Supplier.is_active.is_(True)),
)
