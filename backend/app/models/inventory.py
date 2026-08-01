"""ORM mapping for public.inventory.

Maps 1:1 onto supabase/migrations/20260801100010_inventory.sql, plus the two
cross-table indexes migration 17 adds against this table.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.inventory_movement import InventoryMovement
    from app.models.supplier import Supplier
    from app.models.transaction_item import TransactionItem


class Inventory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "inventory"
    __mapper_args__ = {"eager_defaults": True}

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
    )
    sku: Mapped[str | None] = mapped_column(String(50))
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pcs")
    current_quantity: Mapped[float] = mapped_column(
        Numeric(14, 3), nullable=False, server_default="0"
    )
    reorder_level: Mapped[float] = mapped_column(
        Numeric(14, 3), nullable=False, server_default="0"
    )
    unit_cost: Mapped[float | None] = mapped_column(Numeric(12, 2))
    selling_price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    image_url: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="inventory_items"
    )
    supplier: Mapped["Supplier | None"] = relationship(back_populates="inventory_items")
    transaction_items: Mapped[list["TransactionItem"]] = relationship(
        back_populates="inventory_item"
    )
    movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="inventory_item"
    )


Index("idx_inventory_business_profile", Inventory.business_profile_id)
Index("idx_inventory_supplier", Inventory.supplier_id)
Index(
    "idx_inventory_active",
    Inventory.business_profile_id,
    postgresql_where=(Inventory.is_active.is_(True)),
)
Index(
    "idx_inventory_low_stock",
    Inventory.business_profile_id,
    postgresql_where=(Inventory.current_quantity <= Inventory.reorder_level),
)
Index(
    "uq_inventory_business_sku",
    Inventory.business_profile_id,
    Inventory.sku,
    unique=True,
    postgresql_where=(Inventory.sku.isnot(None)),
)
# From supabase/migrations/20260801100017_performance_indexes.sql.
Index("idx_inventory_profile_name", Inventory.business_profile_id, Inventory.item_name)
