"""Endpoint-level tests for Brand Assets CRUD.

BrandAssetService is replaced via FastAPI's dependency_overrides with an
in-memory fake, so these tests exercise routing, status codes and response
shapes without a live database. Uses the shared `client` fixture from
tests/conftest.py (an in-process ASGI client against the real app).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.api.v1.endpoints import brand_assets as endpoint_module
from app.main import app
from app.models.brand_asset import BrandAsset
from app.models.enums import BrandAssetStatus
from app.services.brand_asset import BrandAssetNotFoundError, InvalidReferenceError

BASE_URL = "/api/v1/brand-assets"


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, BrandAsset] = {}
        self.raise_on_create: Exception | None = None

    async def create(self, payload):
        if self.raise_on_create:
            raise self.raise_on_create
        now = datetime.now(timezone.utc)
        asset = BrandAsset(
            id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump()
        )
        self.store[asset.id] = asset
        return asset

    async def get(self, brand_asset_id):
        asset = self.store.get(brand_asset_id)
        if asset is None:
            raise BrandAssetNotFoundError(str(brand_asset_id))
        return asset

    async def list(self, business_profile_id, *, status=None, limit=20, offset=0):
        items = [
            a
            for a in self.store.values()
            if a.business_profile_id == business_profile_id
        ]
        if status is not None:
            items = [a for a in items if a.status == status]
        return items[offset : offset + limit], len(items)

    async def update(self, brand_asset_id, payload):
        asset = await self.get(brand_asset_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(asset, field, value)
        return asset

    async def delete(self, brand_asset_id):
        asset = await self.get(brand_asset_id)
        asset.status = BrandAssetStatus.ARCHIVED


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


async def test_create_returns_201_with_created_asset(client, fake_service):
    business_profile_id = str(uuid.uuid4())

    response = await client.post(
        BASE_URL,
        json={"business_profile_id": business_profile_id, "brand_name": "AnitaWeaves"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["brand_name"] == "AnitaWeaves"
    assert body["business_profile_id"] == business_profile_id
    assert body["status"] == "draft"
    assert "id" in body and "created_at" in body


async def test_create_invalid_payload_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "brand_name": ""},
    )

    assert response.status_code == 422


async def test_create_missing_required_field_returns_422(client, fake_service):
    response = await client.post(BASE_URL, json={"brand_name": "No business id"})

    assert response.status_code == 422


async def test_create_invalid_reference_returns_422(client, fake_service):
    fake_service.raise_on_create = InvalidReferenceError(
        "business_profile_id does not reference an existing business profile."
    )

    response = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "brand_name": "Test"},
    )

    assert response.status_code == 422


async def test_get_missing_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_existing_returns_200(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "brand_name": "Test Brand"},
    )
    asset_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{asset_id}")

    assert response.status_code == 200
    assert response.json()["brand_name"] == "Test Brand"


async def test_list_without_business_profile_id_returns_422(client, fake_service):
    response = await client.get(BASE_URL)

    assert response.status_code == 422


async def test_list_returns_only_matching_business_profile(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    other_business_profile_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={"business_profile_id": business_profile_id, "brand_name": "Mine"},
    )
    await client.post(
        BASE_URL,
        json={"business_profile_id": other_business_profile_id, "brand_name": "Theirs"},
    )

    response = await client.get(
        BASE_URL, params={"business_profile_id": business_profile_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["brand_name"] == "Mine"


async def test_update_applies_partial_fields(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "brand_name": "Old Name",
            "tagline": "Handloom, reimagined",
        },
    )
    asset_id = create_resp.json()["id"]

    response = await client.patch(
        f"{BASE_URL}/{asset_id}", json={"brand_name": "New Name"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["brand_name"] == "New Name"
    assert body["tagline"] == "Handloom, reimagined"


async def test_update_missing_returns_404(client, fake_service):
    response = await client.patch(
        f"{BASE_URL}/{uuid.uuid4()}", json={"brand_name": "X"}
    )

    assert response.status_code == 404


async def test_delete_returns_204_and_archives(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "brand_name": "Test Brand"},
    )
    asset_id = create_resp.json()["id"]

    response = await client.delete(f"{BASE_URL}/{asset_id}")

    assert response.status_code == 204
    assert fake_service.store[uuid.UUID(asset_id)].status == BrandAssetStatus.ARCHIVED


async def test_delete_missing_returns_404(client, fake_service):
    response = await client.delete(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_openapi_schema_documents_brand_assets_routes(client, fake_service):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/{{brand_asset_id}}" in paths
    assert set(paths[BASE_URL]) >= {"post", "get"}
    assert set(paths[f"{BASE_URL}/{{brand_asset_id}}"]) >= {"get", "patch", "delete"}
