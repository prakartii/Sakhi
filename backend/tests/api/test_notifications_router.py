"""Endpoint-level tests for the Notification API.

NotificationService is replaced via FastAPI's dependency_overrides with an
in-memory fake, so these tests exercise routing, status codes and response
shapes without a live database. Uses the shared `client` fixture from
tests/conftest.py (an in-process ASGI client against the real app).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.api.v1.endpoints import notifications as endpoint_module
from app.main import app
from app.models.enums import NotificationChannel
from app.models.notification import Notification
from app.services.notification import InvalidReferenceError, NotificationNotFoundError

BASE_URL = "/api/v1/notifications"


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, Notification] = {}
        self.raise_on_create: Exception | None = None

    async def create(self, payload):
        if self.raise_on_create:
            raise self.raise_on_create
        now = datetime.now(timezone.utc)
        notification = Notification(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            channel=NotificationChannel.IN_APP,
            is_read=False,
            read_at=None,
            sent_at=None,
            **payload.model_dump(),
        )
        self.store[notification.id] = notification
        return notification

    async def get(self, notification_id):
        notification = self.store.get(notification_id)
        if notification is None:
            raise NotificationNotFoundError(str(notification_id))
        return notification

    async def list(
        self,
        user_id,
        *,
        business_profile_id=None,
        notification_type=None,
        status=None,
        limit=20,
        offset=0,
    ):
        items = [n for n in self.store.values() if n.user_id == user_id]
        if business_profile_id is not None:
            items = [n for n in items if n.business_profile_id == business_profile_id]
        if notification_type is not None:
            items = [n for n in items if n.notification_type == notification_type]
        if status is not None:
            is_read = status == "read"
            items = [n for n in items if n.is_read == is_read]
        return items[offset : offset + limit], len(items)

    async def mark_read(self, notification_id):
        notification = await self.get(notification_id)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
        return notification

    async def mark_all_read(self, user_id):
        updated = 0
        for notification in self.store.values():
            if notification.user_id == user_id and not notification.is_read:
                notification.is_read = True
                notification.read_at = datetime.now(timezone.utc)
                updated += 1
        return updated

    async def delete(self, notification_id):
        notification = await self.get(notification_id)
        del self.store[notification.id]


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


async def test_create_returns_201_with_created_notification(client, fake_service):
    user_id = str(uuid.uuid4())

    response = await client.post(
        BASE_URL,
        json={
            "user_id": user_id,
            "notification_type": "system",
            "title": "Welcome to Sakhi",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == user_id
    assert body["title"] == "Welcome to Sakhi"
    assert body["status"] == "unread"
    assert body["priority"] == "normal"
    assert "id" in body and "created_at" in body


async def test_create_invalid_payload_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL,
        json={"user_id": str(uuid.uuid4()), "notification_type": "system", "title": ""},
    )

    assert response.status_code == 422


async def test_create_missing_required_field_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL, json={"user_id": str(uuid.uuid4()), "title": "No type"}
    )

    assert response.status_code == 422


async def test_create_invalid_reference_returns_422(client, fake_service):
    fake_service.raise_on_create = InvalidReferenceError(
        "user_id does not reference an existing user."
    )

    response = await client.post(
        BASE_URL,
        json={
            "user_id": str(uuid.uuid4()),
            "notification_type": "system",
            "title": "Welcome",
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
            "user_id": str(uuid.uuid4()),
            "notification_type": "inventory_alert",
            "title": "Low stock: Dupatta - Indigo",
        },
    )
    notification_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{notification_id}")

    assert response.status_code == 200
    assert response.json()["notification_type"] == "inventory_alert"


async def test_list_without_user_id_returns_422(client, fake_service):
    response = await client.get(BASE_URL)

    assert response.status_code == 422


async def test_list_returns_only_matching_user(client, fake_service):
    user_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={"user_id": user_id, "notification_type": "system", "title": "Mine"},
    )
    await client.post(
        BASE_URL,
        json={
            "user_id": other_user_id,
            "notification_type": "system",
            "title": "Not mine",
        },
    )

    response = await client.get(BASE_URL, params={"user_id": user_id})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Mine"


async def test_list_filters_by_type(client, fake_service):
    user_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={
            "user_id": user_id,
            "notification_type": "cashflow_alert",
            "title": "Low cashflow",
        },
    )
    await client.post(
        BASE_URL,
        json={
            "user_id": user_id,
            "notification_type": "inventory_alert",
            "title": "Low stock",
        },
    )

    response = await client.get(
        BASE_URL, params={"user_id": user_id, "notification_type": "cashflow_alert"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["notification_type"] == "cashflow_alert"


async def test_list_filters_by_status(client, fake_service):
    user_id = str(uuid.uuid4())
    create_resp = await client.post(
        BASE_URL,
        json={"user_id": user_id, "notification_type": "system", "title": "First"},
    )
    await client.post(
        BASE_URL,
        json={"user_id": user_id, "notification_type": "system", "title": "Second"},
    )
    notification_id = create_resp.json()["id"]
    await client.patch(f"{BASE_URL}/{notification_id}/read")

    unread_resp = await client.get(
        BASE_URL, params={"user_id": user_id, "status": "unread"}
    )
    read_resp = await client.get(
        BASE_URL, params={"user_id": user_id, "status": "read"}
    )

    assert unread_resp.json()["total"] == 1
    assert unread_resp.json()["items"][0]["title"] == "Second"
    assert read_resp.json()["total"] == 1
    assert read_resp.json()["items"][0]["title"] == "First"


async def test_mark_read_returns_updated_notification(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "user_id": str(uuid.uuid4()),
            "notification_type": "system",
            "title": "Welcome",
        },
    )
    notification_id = create_resp.json()["id"]

    response = await client.patch(f"{BASE_URL}/{notification_id}/read")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "read"
    assert body["read_at"] is not None


async def test_mark_read_missing_returns_404(client, fake_service):
    response = await client.patch(f"{BASE_URL}/{uuid.uuid4()}/read")

    assert response.status_code == 404


async def test_mark_all_read_updates_count_and_marks_rows(client, fake_service):
    user_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={"user_id": user_id, "notification_type": "system", "title": "One"},
    )
    await client.post(
        BASE_URL,
        json={"user_id": user_id, "notification_type": "system", "title": "Two"},
    )

    response = await client.post(
        f"{BASE_URL}/mark-all-read", params={"user_id": user_id}
    )

    assert response.status_code == 200
    assert response.json()["updated_count"] == 2

    list_resp = await client.get(
        BASE_URL, params={"user_id": user_id, "status": "unread"}
    )
    assert list_resp.json()["total"] == 0


async def test_mark_all_read_without_user_id_returns_422(client, fake_service):
    response = await client.post(f"{BASE_URL}/mark-all-read")

    assert response.status_code == 422


async def test_delete_returns_204_and_removes_the_row(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "user_id": str(uuid.uuid4()),
            "notification_type": "system",
            "title": "Bye",
        },
    )
    notification_id = create_resp.json()["id"]

    response = await client.delete(f"{BASE_URL}/{notification_id}")

    assert response.status_code == 204
    assert uuid.UUID(notification_id) not in fake_service.store


async def test_delete_missing_returns_404(client, fake_service):
    response = await client.delete(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_openapi_schema_documents_notifications_routes(client, fake_service):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/{{notification_id}}" in paths
    assert f"{BASE_URL}/{{notification_id}}/read" in paths
    assert f"{BASE_URL}/mark-all-read" in paths
    assert set(paths[BASE_URL]) >= {"post", "get"}
    assert set(paths[f"{BASE_URL}/{{notification_id}}"]) >= {"get", "delete"}
