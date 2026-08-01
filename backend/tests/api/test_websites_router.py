"""Endpoint-level tests for Website Management CRUD + version history.

WebsiteService is replaced via FastAPI's dependency_overrides with an
in-memory fake, so these tests exercise routing, status codes and response
shapes without a live database. Uses the shared `client` fixture from
tests/conftest.py (an in-process ASGI client against the real app).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.api.v1.endpoints import websites as endpoint_module
from app.main import app
from app.models.enums import WebsiteStatus
from app.models.website import Website
from app.models.website_version import WebsiteVersion
from app.services.website import (
    InvalidReferenceError,
    WebsiteConflictError,
    WebsiteNotFoundError,
    WebsiteVersionNotFoundError,
)

BASE_URL = "/api/v1/websites"

_SNAPSHOT_FIELDS = (
    "website_name",
    "deployment_url",
    "github_repository",
    "template",
    "status",
    "seo_title",
    "seo_description",
    "custom_domain",
    "favicon",
    "published",
)


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, Website] = {}
        self.versions: list[WebsiteVersion] = []
        self.raise_on_create: Exception | None = None

    async def create(self, payload):
        if self.raise_on_create:
            raise self.raise_on_create
        now = datetime.now(timezone.utc)
        website = Website(
            id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump()
        )
        self.store[website.id] = website
        self._record_version(website, change_notes="Initial version")
        return website

    async def get(self, website_id):
        website = self.store.get(website_id)
        if website is None:
            raise WebsiteNotFoundError(str(website_id))
        return website

    async def list(
        self, business_profile_id, *, status=None, published=None, limit=20, offset=0
    ):
        items = [
            w
            for w in self.store.values()
            if w.business_profile_id == business_profile_id
        ]
        if status is not None:
            items = [w for w in items if w.status == status]
        if published is not None:
            items = [w for w in items if w.published == published]
        return items[offset : offset + limit], len(items)

    async def update(self, website_id, payload):
        website = await self.get(website_id)
        data = payload.model_dump(exclude_unset=True)
        change_notes = data.pop("change_notes", None)
        for field, value in data.items():
            setattr(website, field, value)
        self._record_version(website, change_notes=change_notes)
        return website

    async def delete(self, website_id):
        website = await self.get(website_id)
        website.status = WebsiteStatus.ARCHIVED
        self._record_version(website, change_notes="Archived")

    async def list_versions(self, website_id, *, limit=20, offset=0):
        await self.get(website_id)
        items = sorted(
            (v for v in self.versions if v.website_id == website_id),
            key=lambda v: v.version_number,
            reverse=True,
        )
        return items[offset : offset + limit], len(items)

    async def get_version(self, website_id, version_number):
        await self.get(website_id)
        for v in self.versions:
            if v.website_id == website_id and v.version_number == version_number:
                return v
        raise WebsiteVersionNotFoundError(f"{website_id}/{version_number}")

    def _record_version(self, website, *, change_notes):
        existing = [v for v in self.versions if v.website_id == website.id]
        now = datetime.now(timezone.utc)
        version = WebsiteVersion(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            website_id=website.id,
            version_number=len(existing) + 1,
            change_notes=change_notes,
            **{field: getattr(website, field) for field in _SNAPSHOT_FIELDS},
        )
        self.versions.append(version)


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


async def test_create_returns_201_with_created_website(client, fake_service):
    business_profile_id = str(uuid.uuid4())

    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "website_name": "AnitaWeaves Store",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["website_name"] == "AnitaWeaves Store"
    assert body["business_profile_id"] == business_profile_id
    assert body["status"] == "draft"
    assert "id" in body and "created_at" in body


async def test_create_invalid_payload_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "website_name": ""},
    )

    assert response.status_code == 422


async def test_create_missing_required_field_returns_422(client, fake_service):
    response = await client.post(BASE_URL, json={"website_name": "No business id"})

    assert response.status_code == 422


async def test_create_conflict_returns_409(client, fake_service):
    fake_service.raise_on_create = WebsiteConflictError(
        "custom_domain is already in use by another website."
    )

    response = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "website_name": "Test"},
    )

    assert response.status_code == 409


async def test_create_invalid_reference_returns_422(client, fake_service):
    fake_service.raise_on_create = InvalidReferenceError(
        "business_profile_id does not reference an existing business profile."
    )

    response = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "website_name": "Test"},
    )

    assert response.status_code == 422


async def test_get_missing_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_existing_returns_200(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "website_name": "Test Site"},
    )
    website_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{website_id}")

    assert response.status_code == 200
    assert response.json()["website_name"] == "Test Site"


async def test_list_without_business_profile_id_returns_422(client, fake_service):
    response = await client.get(BASE_URL)

    assert response.status_code == 422


async def test_list_returns_only_matching_business_profile(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    other_business_profile_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={"business_profile_id": business_profile_id, "website_name": "Mine"},
    )
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": other_business_profile_id,
            "website_name": "Theirs",
        },
    )

    response = await client.get(
        BASE_URL, params={"business_profile_id": business_profile_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["website_name"] == "Mine"


async def test_update_applies_partial_fields(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "website_name": "Old Name",
            "template": "boutique-classic",
        },
    )
    website_id = create_resp.json()["id"]

    response = await client.patch(
        f"{BASE_URL}/{website_id}", json={"website_name": "New Name"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["website_name"] == "New Name"
    assert body["template"] == "boutique-classic"


async def test_update_missing_returns_404(client, fake_service):
    response = await client.patch(
        f"{BASE_URL}/{uuid.uuid4()}", json={"website_name": "X"}
    )

    assert response.status_code == 404


async def test_delete_returns_204_and_archives(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "website_name": "Test Site"},
    )
    website_id = create_resp.json()["id"]

    response = await client.delete(f"{BASE_URL}/{website_id}")

    assert response.status_code == 204
    assert fake_service.store[uuid.UUID(website_id)].status == WebsiteStatus.ARCHIVED


async def test_delete_missing_returns_404(client, fake_service):
    response = await client.delete(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_list_versions_returns_history_newest_first(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "website_name": "v1"},
    )
    website_id = create_resp.json()["id"]
    await client.patch(f"{BASE_URL}/{website_id}", json={"website_name": "v2"})

    response = await client.get(f"{BASE_URL}/{website_id}/versions")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert [item["version_number"] for item in body["items"]] == [2, 1]


async def test_list_versions_missing_website_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}/versions")

    assert response.status_code == 404


async def test_get_version_returns_the_requested_snapshot(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "website_name": "v1"},
    )
    website_id = create_resp.json()["id"]
    await client.patch(f"{BASE_URL}/{website_id}", json={"website_name": "v2"})

    response = await client.get(f"{BASE_URL}/{website_id}/versions/1")

    assert response.status_code == 200
    assert response.json()["website_name"] == "v1"


async def test_get_version_missing_returns_404(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={"business_profile_id": str(uuid.uuid4()), "website_name": "v1"},
    )
    website_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{website_id}/versions/99")

    assert response.status_code == 404


async def test_openapi_schema_documents_websites_routes(client, fake_service):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/{{website_id}}" in paths
    assert f"{BASE_URL}/{{website_id}}/versions" in paths
    assert f"{BASE_URL}/{{website_id}}/versions/{{version_number}}" in paths
    assert set(paths[BASE_URL]) >= {"post", "get"}
    assert set(paths[f"{BASE_URL}/{{website_id}}"]) >= {"get", "patch", "delete"}
