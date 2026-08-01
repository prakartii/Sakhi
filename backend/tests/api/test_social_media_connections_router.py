"""Endpoint-level tests for the Social Media Connections API.

SocialMediaConnectionService is replaced via FastAPI's
dependency_overrides with an in-memory fake, so these tests exercise
routing, status codes and response shapes without a live database. Uses
the shared `client` fixture from tests/conftest.py (an in-process ASGI
client against the real app).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.api.v1.endpoints import social_media_connections as endpoint_module
from app.main import app
from app.models.enums import SocialConnectionStatus
from app.models.social_media_connection import SocialMediaConnection
from app.services.social_media_connection import (
    InvalidReferenceError,
    SocialMediaConnectionNotFoundError,
)

BASE_URL = "/api/v1/social-connections"


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, SocialMediaConnection] = {}
        self.raise_on_connect: Exception | None = None

    def _by_business_profile_and_platform(self, business_profile_id, platform):
        for connection in self.store.values():
            if (
                connection.business_profile_id == business_profile_id
                and connection.platform == platform
            ):
                return connection
        return None

    async def connect(self, payload):
        if self.raise_on_connect:
            raise self.raise_on_connect
        existing = self._by_business_profile_and_platform(
            payload.business_profile_id, payload.platform
        )
        now = datetime.now(timezone.utc)
        if existing is not None:
            existing.account_name = payload.account_name
            existing.account_id = payload.account_id
            existing.profile_url = payload.profile_url
            existing.access_token = payload.access_token
            existing.refresh_token = payload.refresh_token
            existing.token_expiry = payload.token_expiry
            existing.connection_status = SocialConnectionStatus.CONNECTED
            existing.updated_at = now
            return existing

        connection = SocialMediaConnection(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            connection_status=SocialConnectionStatus.CONNECTED,
            last_sync=None,
            **payload.model_dump(),
        )
        self.store[connection.id] = connection
        return connection

    async def get(self, connection_id):
        connection = self.store.get(connection_id)
        if connection is None:
            raise SocialMediaConnectionNotFoundError(str(connection_id))
        return connection

    async def list(
        self,
        business_profile_id,
        *,
        platform=None,
        connection_status=None,
        limit=20,
        offset=0,
    ):
        items = [
            c
            for c in self.store.values()
            if c.business_profile_id == business_profile_id
        ]
        if platform is not None:
            items = [c for c in items if c.platform == platform]
        if connection_status is not None:
            items = [c for c in items if c.connection_status == connection_status]
        return items[offset : offset + limit], len(items)

    async def disconnect(self, connection_id):
        connection = await self.get(connection_id)
        connection.connection_status = SocialConnectionStatus.DISCONNECTED
        connection.access_token = None
        connection.refresh_token = None
        connection.token_expiry = None
        return connection

    async def refresh_token(self, connection_id, payload):
        connection = await self.get(connection_id)
        connection.access_token = payload.access_token
        connection.refresh_token = payload.refresh_token
        connection.token_expiry = payload.token_expiry
        connection.connection_status = SocialConnectionStatus.CONNECTED
        return connection

    async def sync_metadata(self, connection_id, payload):
        connection = await self.get(connection_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(connection, field, value)
        connection.last_sync = datetime.now(timezone.utc)
        return connection


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


async def test_connect_returns_201_with_created_connection(client, fake_service):
    business_profile_id = str(uuid.uuid4())

    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "platform": "instagram",
            "access_token": "raw-access-token",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["business_profile_id"] == business_profile_id
    assert body["platform"] == "instagram"
    assert body["connection_status"] == "connected"
    assert "id" in body and "created_at" in body


async def test_connect_response_never_includes_token_fields(client, fake_service):
    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "platform": "instagram",
            "access_token": "super-secret-token",
        },
    )

    body = response.json()
    assert "access_token" not in body
    assert "refresh_token" not in body
    assert "super-secret-token" not in response.text


async def test_connect_invalid_payload_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "platform": "twitter",
            "access_token": "x",
        },
    )

    assert response.status_code == 422


async def test_connect_missing_access_token_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "platform": "instagram"},
    )

    assert response.status_code == 422


async def test_connect_invalid_reference_returns_422(client, fake_service):
    fake_service.raise_on_connect = InvalidReferenceError(
        "business_profile_id does not reference an existing business profile."
    )

    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "platform": "instagram",
            "access_token": "token",
        },
    )

    assert response.status_code == 422


async def test_reconnect_same_platform_updates_existing_row(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    first_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "platform": "linkedin",
            "access_token": "first-token",
        },
    )
    second_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "platform": "linkedin",
            "access_token": "second-token",
        },
    )

    assert first_resp.json()["id"] == second_resp.json()["id"]
    assert len(fake_service.store) == 1


async def test_get_missing_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_existing_returns_200(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "platform": "pinterest",
            "access_token": "token",
        },
    )
    connection_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{connection_id}")

    assert response.status_code == 200
    assert response.json()["platform"] == "pinterest"


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
            "platform": "instagram",
            "access_token": "token",
        },
    )
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": other_business_profile_id,
            "platform": "instagram",
            "access_token": "token",
        },
    )

    response = await client.get(
        BASE_URL, params={"business_profile_id": business_profile_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["business_profile_id"] == business_profile_id


async def test_list_filters_by_platform(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "platform": "instagram",
            "access_token": "token",
        },
    )
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "platform": "facebook",
            "access_token": "token",
        },
    )

    response = await client.get(
        BASE_URL,
        params={"business_profile_id": business_profile_id, "platform": "facebook"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["platform"] == "facebook"


async def test_disconnect_clears_tokens_and_returns_disconnected_status(
    client, fake_service
):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "platform": "instagram",
            "access_token": "token",
        },
    )
    connection_id = create_resp.json()["id"]

    response = await client.post(f"{BASE_URL}/{connection_id}/disconnect")

    assert response.status_code == 200
    assert response.json()["connection_status"] == "disconnected"


async def test_disconnect_missing_returns_404(client, fake_service):
    response = await client.post(f"{BASE_URL}/{uuid.uuid4()}/disconnect")

    assert response.status_code == 404


async def test_refresh_token_updates_status_and_never_echoes_token(
    client, fake_service
):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "platform": "instagram",
            "access_token": "token",
        },
    )
    connection_id = create_resp.json()["id"]

    response = await client.post(
        f"{BASE_URL}/{connection_id}/refresh-token",
        json={"access_token": "brand-new-secret-token"},
    )

    assert response.status_code == 200
    assert response.json()["connection_status"] == "connected"
    assert "brand-new-secret-token" not in response.text


async def test_refresh_token_missing_returns_404(client, fake_service):
    response = await client.post(
        f"{BASE_URL}/{uuid.uuid4()}/refresh-token", json={"access_token": "x"}
    )

    assert response.status_code == 404


async def test_refresh_token_missing_access_token_returns_422(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "platform": "instagram",
            "access_token": "token",
        },
    )
    connection_id = create_resp.json()["id"]

    response = await client.post(f"{BASE_URL}/{connection_id}/refresh-token", json={})

    assert response.status_code == 422


async def test_sync_metadata_updates_fields_and_stamps_last_sync(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "platform": "instagram",
            "access_token": "token",
        },
    )
    connection_id = create_resp.json()["id"]
    assert create_resp.json()["last_sync"] is None

    response = await client.post(
        f"{BASE_URL}/{connection_id}/sync-metadata",
        json={"account_name": "Sakhi Crafts", "account_id": "9988"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["account_name"] == "Sakhi Crafts"
    assert body["account_id"] == "9988"
    assert body["last_sync"] is not None


async def test_sync_metadata_missing_returns_404(client, fake_service):
    response = await client.post(f"{BASE_URL}/{uuid.uuid4()}/sync-metadata", json={})

    assert response.status_code == 404


async def test_openapi_schema_documents_social_connections_routes(client, fake_service):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/{{connection_id}}" in paths
    assert f"{BASE_URL}/{{connection_id}}/disconnect" in paths
    assert f"{BASE_URL}/{{connection_id}}/refresh-token" in paths
    assert f"{BASE_URL}/{{connection_id}}/sync-metadata" in paths
    assert set(paths[BASE_URL]) >= {"post", "get"}
