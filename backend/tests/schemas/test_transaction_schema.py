"""Unit tests for Transaction Pydantic validation. No DB involved."""

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.transaction import TransactionCreate, TransactionUpdate


def _payload(**overrides) -> dict:
    data = {
        "business_profile_id": uuid.uuid4(),
        "transaction_type": "income",
        "amount": 1500.0,
    }
    data.update(overrides)
    return data


def test_minimal_payload_applies_defaults():
    txn = TransactionCreate(**_payload())

    assert txn.amount == 1500.0
    assert txn.currency == "INR"
    assert txn.payment_method.value == "cash"
    assert txn.status.value == "completed"
    assert txn.source.value == "manual"
    assert txn.is_recurring is False
    assert txn.transaction_date == date.today()


def test_negative_amount_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(**_payload(amount=-1))


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(**_payload(not_a_real_field="x"))


def test_missing_transaction_type_rejected():
    payload = _payload()
    del payload["transaction_type"]
    with pytest.raises(ValidationError):
        TransactionCreate(**payload)


@pytest.mark.parametrize(
    "field", ["category", "counterparty_name", "counterparty_contact", "description"]
)
def test_blank_optional_text_fields_normalize_to_none(field):
    txn = TransactionCreate(**_payload(**{field: "   "}))
    assert getattr(txn, field) is None


def test_currency_normalized_to_uppercase():
    txn = TransactionCreate(**_payload(currency="inr"))
    assert txn.currency == "INR"


def test_blank_currency_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(**_payload(currency="   "))


def test_valid_receipt_url_accepted():
    txn = TransactionCreate(**_payload(receipt_url="https://example.com/receipt.pdf"))
    assert txn.receipt_url == "https://example.com/receipt.pdf"


def test_invalid_receipt_url_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(**_payload(receipt_url="not-a-url"))


def test_invalid_transaction_type_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(**_payload(transaction_type="donation"))


def test_update_schema_allows_all_fields_omitted():
    update = TransactionUpdate()
    assert update.model_dump(exclude_unset=True) == {}


def test_update_schema_rejects_explicit_null_for_not_null_column():
    with pytest.raises(ValidationError):
        TransactionUpdate(status=None)


def test_update_schema_tracks_only_provided_fields():
    update = TransactionUpdate(amount=200.0)
    assert update.model_dump(exclude_unset=True) == {"amount": 200.0}


def test_update_schema_allows_amount_and_transaction_type_to_be_omitted():
    update = TransactionUpdate(category="Rent")
    dumped = update.model_dump(exclude_unset=True)
    assert dumped == {"category": "Rent"}
