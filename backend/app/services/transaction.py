"""Business logic for the Finance module (Transaction).

Owns the transaction boundary (commit/rollback) around each use case and
translates database-level failures into domain exceptions the API layer
maps to HTTP status codes — routers never see SQLAlchemy exceptions
directly. Format/shape validation (URL scheme, non-negative amount) lives
in the Pydantic schemas at the API boundary. Two things belong here instead
because they require interpreting the data, not just checking its shape:
translating a foreign-key violation into which reference is bad, and
rejecting a transaction that claims to be recurring with no frequency set.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RecurringFrequency, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.repositories.transaction import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionNotFoundError(Exception):
    """No transactions row exists for the given id."""


class InvalidReferenceError(Exception):
    """A referenced business_profile_id or supplier_id does not exist."""


class InvalidTransactionError(Exception):
    """The transaction data is internally inconsistent, e.g. is_recurring=True
    with no recurring_frequency, or a check constraint the schema enforces
    was somehow bypassed at the API layer."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "transactions_business_profile_id_fkey" in message:
        return InvalidReferenceError(
            "business_profile_id does not reference an existing business profile."
        )
    if "transactions_supplier_id_fkey" in message:
        return InvalidReferenceError(
            "supplier_id does not reference an existing supplier."
        )
    if "chk_transactions_amount_positive" in message:
        return InvalidTransactionError("amount must be greater than or equal to 0.")
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500.
    return exc


def _validate_recurrence(
    *, is_recurring: bool, recurring_frequency: RecurringFrequency | None
) -> None:
    if is_recurring and recurring_frequency is None:
        raise InvalidTransactionError(
            "recurring_frequency is required when is_recurring is true."
        )


class TransactionService:
    def __init__(
        self,
        session: AsyncSession,
        repository: TransactionRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or TransactionRepository(session)

    async def create(self, payload: TransactionCreate) -> Transaction:
        _validate_recurrence(
            is_recurring=payload.is_recurring,
            recurring_frequency=payload.recurring_frequency,
        )
        transaction = Transaction(**payload.model_dump())
        try:
            await self._repo.create(transaction)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return transaction

    async def get(self, transaction_id: uuid.UUID) -> Transaction:
        transaction = await self._repo.get_by_id(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError(str(transaction_id))
        return transaction

    async def list(
        self,
        business_profile_id: uuid.UUID,
        *,
        transaction_type: TransactionType | None = None,
        status: TransactionStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        return await self._repo.list_by_business_profile(
            business_profile_id,
            transaction_type=transaction_type,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def update(
        self, transaction_id: uuid.UUID, payload: TransactionUpdate
    ) -> Transaction:
        """PATCH: applies only the fields the caller actually supplied. The
        recurrence check runs against the resulting merged state (existing
        value for anything the caller didn't touch), not the raw payload —
        setting only is_recurring=true on a transaction that already has a
        recurring_frequency is valid; setting it on one that doesn't isn't.
        """
        transaction = await self.get(transaction_id)
        data = payload.model_dump(exclude_unset=True)
        _validate_recurrence(
            is_recurring=data.get("is_recurring", transaction.is_recurring),
            recurring_frequency=data.get(
                "recurring_frequency", transaction.recurring_frequency
            ),
        )
        try:
            await self._repo.update(transaction, data)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return transaction

    async def delete(self, transaction_id: uuid.UUID) -> None:
        """Hard delete — unlike Business Profile/Brand Assets/Website,
        `status` here (pending/completed/failed/refunded) describes
        payment state, not record lifecycle, so there's no existing value
        that means "soft-deleted," and adding one would be a schema
        change this task explicitly rules out. Safe to delete for real:
        transaction_items cascade automatically (ON DELETE CASCADE) and
        any inventory_movements referencing this transaction have the
        link cleared automatically (ON DELETE SET NULL) — both handled by
        the database, not by this service.
        """
        transaction = await self.get(transaction_id)
        await self._repo.delete(transaction)
        await self._session.commit()
