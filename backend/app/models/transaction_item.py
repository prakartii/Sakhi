"""ORM mapping for public.transaction_items.

Maps 1:1 onto supabase/migrations/20260801100011_cashflow_transactions.sql
(the transaction_items half — see transaction.py for the other table it
defines).
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.inventory import Inventory
    from app.models.transaction import Transaction


class TransactionItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transaction_items"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_transaction_items_quantity_positive"),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
    )
    inventory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inventory.id", ondelete="SET NULL"),
    )
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[float] = mapped_column(
        Numeric(14, 3), nullable=False, server_default="1"
    )
    unit: Mapped[str | None] = mapped_column(String(20))
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)

    # -- relationships ----------------------------------------------------
    transaction: Mapped["Transaction"] = relationship(back_populates="items")
    inventory_item: Mapped["Inventory | None"] = relationship(
        back_populates="transaction_items"
    )


Index("idx_transaction_items_transaction", TransactionItem.transaction_id)
Index("idx_transaction_items_inventory", TransactionItem.inventory_id)
