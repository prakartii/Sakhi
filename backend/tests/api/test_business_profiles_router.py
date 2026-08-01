"""Endpoint-level tests for Business Profile CRUD.

BusinessProfileService is replaced via FastAPI's dependency_overrides with
an in-memory fake, so these tests exercise routing, status codes and
response shapes without a live database. Uses the shared `client` fixture
from tests/conftest.py (an in-process ASGI client against the real app).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.api.v1.endpoints import business_profiles as endpoint_module
from app.main import app
from app.models.business_profile import BusinessProfile
from app.models.enums import BusinessStatus
from app.schemas.business_profile import BusinessProfileOnboardingStatus
from app.services.business_profile import (
    _ONBOARDING_REQUIRED_FIELDS,
    BusinessProfileConflictError,
    BusinessProfileNotFoundError,
)

BASE_URL = "/api/v1/business-profiles"


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, BusinessProfile] = {}
        self.raise_on_create: Exception | None = None

    async def create(self, payload):
        if self.raise_on_create:
            raise self.raise_on_create
        now = datetime.now(timezone.utc)
        profile = BusinessProfile(
            id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump()
        )
        self.store[profile.id] = profile
        return profile

    async def get(self, business_profile_id):
        profile = self.store.get(business_profile_id)
        if profile is None:
            raise BusinessProfileNotFoundError(str(business_profile_id))
        return profile

    async def list(self, user_id, *, status=None, limit=20, offset=0):
        items = [p for p in self.store.values() if p.user_id == user_id]
        if status is not None:
            items = [p for p in items if p.status == status]
        return items[offset : offset + limit], len(items)

    async def update(self, business_profile_id, payload):
        profile = await self.get(business_profile_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        return profile

    async def replace(self, business_profile_id, payload):
        profile = await self.get(business_profile_id)
        for field, value in payload.model_dump().items():
            setattr(profile, field, value)
        return profile

    async def delete(self, business_profile_id):
        profile = await self.get(business_profile_id)
        profile.status = BusinessStatus.ARCHIVED

    async def get_onboarding_status(self, business_profile_id):
        profile = await self.get(business_profile_id)
        completed = [
            field
            for field in _ONBOARDING_REQUIRED_FIELDS
            if getattr(profile, field) not in (None, "")
        ]
        missing = [f for f in _ONBOARDING_REQUIRED_FIELDS if f not in completed]
        return BusinessProfileOnboardingStatus(
            business_profile_id=profile.id,
            is_complete=not missing,
            completion_percentage=round(
                len(completed) / len(_ONBOARDING_REQUIRED_FIELDS) * 100, 2
            ),
            completed_fields=completed,
            missing_fields=missing,
        )


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


async def test_create_returns_201_with_created_profile(client, fake_service):
    user_id = str(uuid.uuid4())

    response = await client.post(
        BASE_URL, json={"user_id": user_id, "business_name": "Anita's Boutique"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["business_name"] == "Anita's Boutique"
    assert body["user_id"] == user_id
    assert body["status"] == "active"
    assert "id" in body and "created_at" in body


async def test_create_invalid_payload_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL, json={"user_id": str(uuid.uuid4()), "business_name": ""}
    )

    assert response.status_code == 422


async def test_create_missing_required_field_returns_422(client, fake_service):
    response = await client.post(BASE_URL, json={"business_name": "No user id"})

    assert response.status_code == 422


async def test_create_conflict_returns_409(client, fake_service):
    fake_service.raise_on_create = BusinessProfileConflictError(
        "already has a primary business profile"
    )

    response = await client.post(
        BASE_URL, json={"user_id": str(uuid.uuid4()), "business_name": "Test"}
    )

    assert response.status_code == 409
    assert "primary" in response.json()["detail"]


async def test_get_missing_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_existing_returns_200(client, fake_service):
    create_resp = await client.post(
        BASE_URL, json={"user_id": str(uuid.uuid4()), "business_name": "Test Biz"}
    )
    profile_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{profile_id}")

    assert response.status_code == 200
    assert response.json()["business_name"] == "Test Biz"


async def test_list_without_user_id_returns_422(client, fake_service):
    response = await client.get(BASE_URL)

    assert response.status_code == 422


async def test_list_returns_only_matching_user(client, fake_service):
    user_id = str(uuid.uuid4())
    other_user_id = str(uuid.uuid4())
    await client.post(BASE_URL, json={"user_id": user_id, "business_name": "Mine"})
    await client.post(
        BASE_URL, json={"user_id": other_user_id, "business_name": "Theirs"}
    )

    response = await client.get(BASE_URL, params={"user_id": user_id})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["business_name"] == "Mine"


async def test_update_applies_partial_fields(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "user_id": str(uuid.uuid4()),
            "business_name": "Old Name",
            "city": "Pune",
        },
    )
    profile_id = create_resp.json()["id"]

    response = await client.patch(
        f"{BASE_URL}/{profile_id}", json={"business_name": "New Name"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["business_name"] == "New Name"
    assert body["city"] == "Pune"


async def test_update_missing_returns_404(client, fake_service):
    response = await client.patch(
        f"{BASE_URL}/{uuid.uuid4()}", json={"business_name": "X"}
    )

    assert response.status_code == 404


async def test_put_replaces_and_resets_omitted_fields(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "user_id": str(uuid.uuid4()),
            "business_name": "Old Name",
            "city": "Pune",
        },
    )
    profile_id = create_resp.json()["id"]

    response = await client.put(
        f"{BASE_URL}/{profile_id}", json={"business_name": "New Name"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["business_name"] == "New Name"
    assert body["city"] is None  # PUT resets fields not in the payload


async def test_put_missing_returns_404(client, fake_service):
    response = await client.put(
        f"{BASE_URL}/{uuid.uuid4()}", json={"business_name": "X"}
    )

    assert response.status_code == 404


async def test_put_invalid_payload_returns_422(client, fake_service):
    create_resp = await client.post(
        BASE_URL, json={"user_id": str(uuid.uuid4()), "business_name": "Test Biz"}
    )
    profile_id = create_resp.json()["id"]

    response = await client.put(
        f"{BASE_URL}/{profile_id}", json={"business_name": "", "website_url": "nope"}
    )

    assert response.status_code == 422


async def test_onboarding_status_returns_200_with_expected_shape(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "user_id": str(uuid.uuid4()),
            "business_name": "Test Biz",
            "owner_name": "Meera",
        },
    )
    profile_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{profile_id}/onboarding-status")

    assert response.status_code == 200
    body = response.json()
    assert body["business_profile_id"] == profile_id
    assert body["is_complete"] is False
    assert "owner_name" in body["completed_fields"]
    assert "business_description" in body["missing_fields"]


async def test_onboarding_status_missing_profile_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}/onboarding-status")

    assert response.status_code == 404


async def test_delete_returns_204_and_archives(client, fake_service):
    create_resp = await client.post(
        BASE_URL, json={"user_id": str(uuid.uuid4()), "business_name": "Test Biz"}
    )
    profile_id = create_resp.json()["id"]

    response = await client.delete(f"{BASE_URL}/{profile_id}")

    assert response.status_code == 204
    assert fake_service.store[uuid.UUID(profile_id)].status == BusinessStatus.ARCHIVED


async def test_delete_missing_returns_404(client, fake_service):
    response = await client.delete(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_openapi_schema_documents_business_profiles_routes(client, fake_service):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/{{business_profile_id}}" in paths
    assert f"{BASE_URL}/{{business_profile_id}}/onboarding-status" in paths
    assert set(paths[BASE_URL]) >= {"post", "get"}
    assert set(paths[f"{BASE_URL}/{{business_profile_id}}"]) >= {
        "get",
        "patch",
        "put",
        "delete",
    }
