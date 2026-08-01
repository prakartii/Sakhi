"""ORM mapping for public.transactions.

Maps 1:1 onto supabase/migrations/20260801100011_cashflow_transactions.sql
(the transactions half — see transaction_item.py for the other table it
defines), plus the one cross-table index migration 17 adds against this
table.
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    PaymentMethod,
    RecurringFrequency,
    TransactionSource,
    TransactionStatus,
    TransactionType,
    pg_enum,
)
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.business_profile import BusinessProfile
    from app.models.inventory_movement import InventoryMovement
    from app.models.supplier import Supplier
    from app.models.transaction_item import TransactionItem


class Transaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transactions"
    __mapper_args__ = {"eager_defaults": True}
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_transactions_amount_positive"),
    )

    business_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("business_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("suppliers.id", ondelete="SET NULL"),
    )
    transaction_type: Mapped[TransactionType] = mapped_column(
        pg_enum(TransactionType, "transaction_type_enum"), nullable=False
    )
    category: Mapped[str | None] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="INR"
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        pg_enum(PaymentMethod, "payment_method_enum"),
        nullable=False,
        server_default=PaymentMethod.CASH.value,
    )
    counterparty_name: Mapped[str | None] = mapped_column(String(200))
    counterparty_contact: Mapped[str | None] = mapped_column(String(50))
    transaction_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )
    description: Mapped[str | None] = mapped_column(Text)
    receipt_url: Mapped[str | None] = mapped_column(Text)
    is_recurring: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    recurring_frequency: Mapped[RecurringFrequency | None] = mapped_column(
        pg_enum(RecurringFrequency, "recurring_frequency_enum")
    )
    status: Mapped[TransactionStatus] = mapped_column(
        pg_enum(TransactionStatus, "transaction_status_enum"),
        nullable=False,
        server_default=TransactionStatus.COMPLETED.value,
    )
    source: Mapped[TransactionSource] = mapped_column(
        pg_enum(TransactionSource, "transaction_source_enum"),
        nullable=False,
        server_default=TransactionSource.MANUAL.value,
    )

    # -- relationships ----------------------------------------------------
    business_profile: Mapped["BusinessProfile"] = relationship(
        back_populates="transactions"
    )
    supplier: Mapped["Supplier | None"] = relationship(back_populates="transactions")
    items: Mapped[list["TransactionItem"]] = relationship(back_populates="transaction")
    inventory_movements: Mapped[list["InventoryMovement"]] = relationship(
        back_populates="related_transaction"
    )


Index(
    "idx_transactions_business_profile_date",
    Transaction.business_profile_id,
    Transaction.transaction_date.desc(),
)
Index(
    "idx_transactions_type",
    Transaction.business_profile_id,
    Transaction.transaction_type,
)
Index("idx_transactions_supplier", Transaction.supplier_id)
Index(
    "idx_transactions_status",
    Transaction.status,
    postgresql_where=(Transaction.status == TransactionStatus.PENDING),
)
# From supabase/migrations/20260801100017_performance_indexes.sql.
Index(
    "idx_transactions_profile_type_date",
    Transaction.business_profile_id,
    Transaction.transaction_type,
    Transaction.transaction_date.desc(),
)
