"""ORM mapping for public.inventory_movements.

Maps 1:1 onto supabase/migrations/20260801100012_inventory_movements.sql.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import InventoryMovementType, pg_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.inventory import Inventory
    from app.models.transaction import Transaction


class InventoryMovement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "inventory_movements"
    __mapper_args__ = {"eager_defaults": True}

    inventory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory.id", ondelete="CASCADE"),
        nullable=False,
    )
    related_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
    )
    movement_type: Mapped[InventoryMovementType] = mapped_column(
        pg_enum(InventoryMovementType, "inventory_movement_type_enum"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    quantity_before: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    quantity_after: Mapped[float] = mapped_column(Numeric(14, 3), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    movement_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # -- relationships ----------------------------------------------------
    inventory_item: Mapped["Inventory"] = relationship(back_populates="movements")
    related_transaction: Mapped["Transaction | None"] = relationship(
        back_populates="inventory_movements"
    )


Index(
    "idx_inventory_movements_inventory",
    InventoryMovement.inventory_id,
    InventoryMovement.movement_date.desc(),
)
Index("idx_inventory_movements_transaction", InventoryMovement.related_transaction_id)
Index("idx_inventory_movements_type", InventoryMovement.movement_type)
