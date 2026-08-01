"""Unit tests for TransactionService. Both the repository and the DB
session are faked/mocked — no database connection is used or required.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import RecurringFrequency, TransactionStatus, TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.transaction import (
    InvalidReferenceError,
    InvalidTransactionError,
    TransactionNotFoundError,
    TransactionService,
)


class _FakeRepository:
    """In-memory stand-in for TransactionRepository."""

    def __init__(self) -> None:
        self.store: dict[uuid.UUID, Transaction] = {}
        self.raise_on_write: Exception | None = None
        self.deleted: list[uuid.UUID] = []

    async def create(self, transaction: Transaction) -> Transaction:
        if self.raise_on_write:
            raise self.raise_on_write
        transaction.id = transaction.id or uuid.uuid4()
        self.store[transaction.id] = transaction
        return transaction

    async def get_by_id(self, transaction_id: uuid.UUID) -> Transaction | None:
        return self.store.get(transaction_id)

    async def update(self, transaction: Transaction, data: dict) -> Transaction:
        if self.raise_on_write:
            raise self.raise_on_write
        for field, value in data.items():
            setattr(transaction, field, value)
        return transaction

    async def delete(self, transaction: Transaction) -> None:
        self.deleted.append(transaction.id)
        self.store.pop(transaction.id, None)

    async def list_by_business_profile(
        self,
        business_profile_id,
        *,
        transaction_type=None,
        status=None,
        limit=20,
        offset=0,
    ):
        items = [
            t
            for t in self.store.values()
            if t.business_profile_id == business_profile_id
        ]
        if transaction_type is not None:
            items = [t for t in items if t.transaction_type == transaction_type]
        if status is not None:
            items = [t for t in items if t.status == status]
        return items[offset : offset + limit], len(items)


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _make_service():
    repo = _FakeRepository()
    session = AsyncMock()
    return TransactionService(session, repository=repo), repo, session


def _create_payload(**overrides) -> TransactionCreate:
    data = {
        "business_profile_id": uuid.uuid4(),
        "transaction_type": TransactionType.INCOME,
        "amount": 1500.0,
    }
    data.update(overrides)
    return TransactionCreate(**data)


async def test_create_persists_and_commits():
    service, repo, session = _make_service()

    result = await service.create(_create_payload())

    assert result.amount == 1500.0
    assert result.id in repo.store
    session.commit.assert_awaited_once()


async def test_get_missing_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(TransactionNotFoundError):
        await service.get(uuid.uuid4())


async def test_get_existing_returns_transaction():
    service, _repo, _session = _make_service()
    created = await service.create(_create_payload())

    fetched = await service.get(created.id)

    assert fetched is created


async def test_create_rejects_recurring_without_frequency():
    service, _repo, _session = _make_service()

    with pytest.raises(InvalidTransactionError):
        await service.create(_create_payload(is_recurring=True))


async def test_create_accepts_recurring_with_frequency():
    service, _repo, _session = _make_service()

    result = await service.create(
        _create_payload(
            is_recurring=True, recurring_frequency=RecurringFrequency.MONTHLY
        )
    )

    assert result.is_recurring is True
    assert result.recurring_frequency == RecurringFrequency.MONTHLY


async def test_create_translates_invalid_business_profile_reference():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "transactions" violates foreign key '
        'constraint "transactions_business_profile_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload())


async def test_create_translates_invalid_supplier_reference():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "transactions" violates foreign key '
        'constraint "transactions_supplier_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload(supplier_id=uuid.uuid4()))


async def test_create_reraises_unrecognized_integrity_error():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error("some_other_constraint_violation")

    with pytest.raises(IntegrityError):
        await service.create(_create_payload())


async def test_update_applies_only_provided_fields():
    service, _repo, session = _make_service()
    created = await service.create(_create_payload(category="Sales"))

    updated = await service.update(created.id, TransactionUpdate(amount=2000.0))

    assert updated.amount == 2000.0
    assert updated.category == "Sales"  # untouched
    session.commit.assert_awaited()


async def test_update_missing_transaction_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(TransactionNotFoundError):
        await service.update(uuid.uuid4(), TransactionUpdate(amount=1.0))


async def test_update_rejects_recurring_with_no_frequency_from_existing_state():
    service, _repo, _session = _make_service()
    created = await service.create(_create_payload())  # is_recurring=False by default

    with pytest.raises(InvalidTransactionError):
        await service.update(created.id, TransactionUpdate(is_recurring=True))


async def test_update_allows_recurring_true_when_frequency_already_set():
    service, _repo, _session = _make_service()
    created = await service.create(
        _create_payload(
            is_recurring=True, recurring_frequency=RecurringFrequency.WEEKLY
        )
    )

    # Only toggling category — recurring_frequency already satisfies the rule
    # from the existing row, so this must not raise.
    updated = await service.update(created.id, TransactionUpdate(category="Utilities"))

    assert updated.category == "Utilities"
    assert updated.is_recurring is True


async def test_delete_removes_the_row():
    service, repo, session = _make_service()
    created = await service.create(_create_payload())

    await service.delete(created.id)

    assert created.id not in repo.store
    assert created.id in repo.deleted
    session.commit.assert_awaited()


async def test_delete_missing_transaction_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(TransactionNotFoundError):
        await service.delete(uuid.uuid4())


async def test_list_filters_by_business_profile_and_type():
    service, _repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    other_business_profile_id = uuid.uuid4()
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            transaction_type=TransactionType.INCOME,
        )
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            transaction_type=TransactionType.EXPENSE,
        )
    )
    await service.create(_create_payload(business_profile_id=other_business_profile_id))

    income_items, income_total = await service.list(
        business_profile_id, transaction_type=TransactionType.INCOME
    )
    all_items, all_total = await service.list(business_profile_id)

    assert income_total == 1
    assert income_items[0].transaction_type == TransactionType.INCOME
    assert all_total == 2


async def test_list_filters_by_status():
    service, _repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id, status=TransactionStatus.PENDING
        )
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id, status=TransactionStatus.COMPLETED
        )
    )

    pending_items, pending_total = await service.list(
        business_profile_id, status=TransactionStatus.PENDING
    )

    assert pending_total == 1
    assert pending_items[0].status == TransactionStatus.PENDING
