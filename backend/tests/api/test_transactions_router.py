"""Endpoint-level tests for the Finance (Transaction) CRUD API.

TransactionService is replaced via FastAPI's dependency_overrides with an
in-memory fake, so these tests exercise routing, status codes and response
shapes without a live database. Uses the shared `client` fixture from
tests/conftest.py (an in-process ASGI client against the real app).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.api.v1.endpoints import transactions as endpoint_module
from app.main import app
from app.models.transaction import Transaction
from app.services.transaction import (
    InvalidReferenceError,
    InvalidTransactionError,
    TransactionNotFoundError,
)

BASE_URL = "/api/v1/transactions"


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, Transaction] = {}
        self.raise_on_create: Exception | None = None

    async def create(self, payload):
        if self.raise_on_create:
            raise self.raise_on_create
        now = datetime.now(timezone.utc)
        txn = Transaction(
            id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump()
        )
        self.store[txn.id] = txn
        return txn

    async def get(self, transaction_id):
        txn = self.store.get(transaction_id)
        if txn is None:
            raise TransactionNotFoundError(str(transaction_id))
        return txn

    async def list(
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

    async def update(self, transaction_id, payload):
        txn = await self.get(transaction_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(txn, field, value)
        return txn

    async def delete(self, transaction_id):
        txn = await self.get(transaction_id)
        del self.store[txn.id]


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


async def test_create_returns_201_with_created_transaction(client, fake_service):
    business_profile_id = str(uuid.uuid4())

    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "transaction_type": "income",
            "amount": 1500.0,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == 1500.0
    assert body["business_profile_id"] == business_profile_id
    assert body["status"] == "completed"
    assert "id" in body and "created_at" in body


async def test_create_invalid_payload_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "transaction_type": "income",
            "amount": -5,
        },
    )

    assert response.status_code == 422


async def test_create_missing_required_field_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL, json={"business_profile_id": str(uuid.uuid4()), "amount": 100}
    )

    assert response.status_code == 422


async def test_create_invalid_reference_returns_422(client, fake_service):
    fake_service.raise_on_create = InvalidReferenceError(
        "business_profile_id does not reference an existing business profile."
    )

    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "transaction_type": "income",
            "amount": 100,
        },
    )

    assert response.status_code == 422


async def test_create_invalid_recurrence_returns_422(client, fake_service):
    fake_service.raise_on_create = InvalidTransactionError(
        "recurring_frequency is required when is_recurring is true."
    )

    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "transaction_type": "expense",
            "amount": 100,
            "is_recurring": True,
        },
    )

    assert response.status_code == 422


async def test_get_missing_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_existing_returns_200(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "transaction_type": "expense",
            "amount": 250,
        },
    )
    transaction_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{transaction_id}")

    assert response.status_code == 200
    assert response.json()["amount"] == 250.0


async def test_list_without_business_profile_id_returns_422(client, fake_service):
    response = await client.get(BASE_URL)

    assert response.status_code == 422


async def test_list_returns_only_matching_business_profile(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    other_business_profile_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "transaction_type": "income",
            "amount": 100,
        },
    )
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": other_business_profile_id,
            "transaction_type": "income",
            "amount": 200,
        },
    )

    response = await client.get(
        BASE_URL, params={"business_profile_id": business_profile_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["amount"] == 100.0


async def test_list_filters_by_transaction_type(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "transaction_type": "income",
            "amount": 100,
        },
    )
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "transaction_type": "expense",
            "amount": 50,
        },
    )

    response = await client.get(
        BASE_URL,
        params={
            "business_profile_id": business_profile_id,
            "transaction_type": "expense",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["transaction_type"] == "expense"


async def test_update_applies_partial_fields(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "transaction_type": "income",
            "amount": 100,
            "category": "Sales",
        },
    )
    transaction_id = create_resp.json()["id"]

    response = await client.patch(f"{BASE_URL}/{transaction_id}", json={"amount": 300})

    assert response.status_code == 200
    body = response.json()
    assert body["amount"] == 300.0
    assert body["category"] == "Sales"


async def test_update_missing_returns_404(client, fake_service):
    response = await client.patch(f"{BASE_URL}/{uuid.uuid4()}", json={"amount": 1})

    assert response.status_code == 404


async def test_delete_returns_204_and_removes_the_row(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "transaction_type": "income",
            "amount": 100,
        },
    )
    transaction_id = create_resp.json()["id"]

    response = await client.delete(f"{BASE_URL}/{transaction_id}")

    assert response.status_code == 204
    assert uuid.UUID(transaction_id) not in fake_service.store


async def test_delete_missing_returns_404(client, fake_service):
    response = await client.delete(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_openapi_schema_documents_transactions_routes(client, fake_service):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/{{transaction_id}}" in paths
    assert set(paths[BASE_URL]) >= {"post", "get"}
    assert set(paths[f"{BASE_URL}/{{transaction_id}}"]) >= {"get", "patch", "delete"}
