"""Endpoint-level tests for the Content Calendar API.

ContentCalendarItemService is replaced via FastAPI's dependency_overrides
with an in-memory fake, so these tests exercise routing, status codes and
response shapes without a live database. Uses the shared `client` fixture
from tests/conftest.py (an in-process ASGI client against the real app).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.api.v1.endpoints import content_calendar_items as endpoint_module
from app.main import app
from app.models.content_calendar_item import ContentCalendarItem
from app.services.content_calendar_item import (
    ContentCalendarItemNotFoundError,
    InvalidReferenceError,
    InvalidSocialConnectionError,
)

BASE_URL = "/api/v1/content-calendar"


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, ContentCalendarItem] = {}
        self.raise_on_create: Exception | None = None

    async def create(self, payload):
        if self.raise_on_create:
            raise self.raise_on_create
        now = datetime.now(timezone.utc)
        item = ContentCalendarItem(
            id=uuid.uuid4(), created_at=now, updated_at=now, **payload.model_dump()
        )
        self.store[item.id] = item
        return item

    async def get(self, item_id):
        item = self.store.get(item_id)
        if item is None:
            raise ContentCalendarItemNotFoundError(str(item_id))
        return item

    async def list(
        self, business_profile_id, *, platform=None, status=None, limit=20, offset=0
    ):
        items = [
            i
            for i in self.store.values()
            if i.business_profile_id == business_profile_id
        ]
        if platform is not None:
            items = [i for i in items if i.platform == platform]
        if status is not None:
            items = [i for i in items if i.status == status]
        return items[offset : offset + limit], len(items)

    async def search(self, query, *, business_profile_id=None, limit=20, offset=0):
        items = list(self.store.values())
        if business_profile_id is not None:
            items = [i for i in items if i.business_profile_id == business_profile_id]
        needle = query.lower()
        items = [i for i in items if needle in i.title.lower()]
        return items[offset : offset + limit], len(items)

    async def monthly_calendar(
        self,
        business_profile_id,
        *,
        year,
        month,
        platform=None,
        status=None,
        limit=100,
        offset=0,
    ):
        items = [
            i
            for i in self.store.values()
            if i.business_profile_id == business_profile_id
            and i.scheduled_datetime is not None
            and i.scheduled_datetime.year == year
            and i.scheduled_datetime.month == month
        ]
        return items[offset : offset + limit], len(items)

    async def weekly_calendar(
        self,
        business_profile_id,
        *,
        week_start,
        platform=None,
        status=None,
        limit=100,
        offset=0,
    ):
        from datetime import datetime as dt
        from datetime import timedelta

        start = dt.combine(week_start, dt.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=7)
        items = [
            i
            for i in self.store.values()
            if i.business_profile_id == business_profile_id
            and i.scheduled_datetime is not None
            and start <= i.scheduled_datetime < end
        ]
        return items[offset : offset + limit], len(items)

    async def update(self, item_id, payload):
        item = await self.get(item_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        return item

    async def delete(self, item_id):
        item = await self.get(item_id)
        del self.store[item.id]


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


async def test_create_returns_201_with_created_item(client, fake_service):
    business_profile_id = str(uuid.uuid4())

    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "title": "Diwali collection teaser",
            "content_type": "post",
            "platform": "instagram",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["business_profile_id"] == business_profile_id
    assert body["title"] == "Diwali collection teaser"
    assert body["status"] == "draft"
    assert "id" in body and "created_at" in body


async def test_create_invalid_payload_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "title": "",
            "content_type": "post",
            "platform": "instagram",
        },
    )

    assert response.status_code == 422


async def test_create_missing_required_field_returns_422(client, fake_service):
    response = await client.post(
        BASE_URL, json={"business_profile_id": str(uuid.uuid4()), "title": "No type"}
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
            "title": "Post",
            "content_type": "post",
            "platform": "instagram",
        },
    )

    assert response.status_code == 422


async def test_create_invalid_social_connection_returns_422(client, fake_service):
    fake_service.raise_on_create = InvalidSocialConnectionError(
        "social_connection_id's platform does not match this content item's platform."
    )

    response = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "title": "Post",
            "content_type": "post",
            "platform": "instagram",
            "social_connection_id": str(uuid.uuid4()),
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
            "title": "Post",
            "content_type": "reel",
            "platform": "instagram",
        },
    )
    item_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{item_id}")

    assert response.status_code == 200
    assert response.json()["content_type"] == "reel"


async def test_list_without_business_profile_id_returns_422(client, fake_service):
    response = await client.get(BASE_URL)

    assert response.status_code == 422


async def test_list_filters_by_platform_and_status(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "title": "Instagram post",
            "content_type": "post",
            "platform": "instagram",
            "status": "scheduled",
        },
    )
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "title": "Pinterest pin",
            "content_type": "post",
            "platform": "pinterest",
            "status": "draft",
        },
    )

    response = await client.get(
        BASE_URL,
        params={
            "business_profile_id": business_profile_id,
            "platform": "instagram",
            "status": "scheduled",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Instagram post"


async def test_search_returns_matching_items(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "title": "Diwali teaser",
            "content_type": "post",
            "platform": "instagram",
        },
    )
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "title": "New arrivals",
            "content_type": "post",
            "platform": "instagram",
        },
    )

    response = await client.get(
        f"{BASE_URL}/search",
        params={"q": "diwali", "business_profile_id": business_profile_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Diwali teaser"


async def test_monthly_calendar_returns_items_in_that_month(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "title": "March post",
            "content_type": "post",
            "platform": "instagram",
            "scheduled_datetime": "2026-03-15T10:00:00Z",
        },
    )
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "title": "April post",
            "content_type": "post",
            "platform": "instagram",
            "scheduled_datetime": "2026-04-01T10:00:00Z",
        },
    )

    response = await client.get(
        f"{BASE_URL}/monthly",
        params={"business_profile_id": business_profile_id, "year": 2026, "month": 3},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "March post"


async def test_weekly_calendar_returns_items_in_that_week(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "title": "In week",
            "content_type": "post",
            "platform": "instagram",
            "scheduled_datetime": "2026-03-04T10:00:00Z",
        },
    )
    await client.post(
        BASE_URL,
        json={
            "business_profile_id": business_profile_id,
            "title": "Out of week",
            "content_type": "post",
            "platform": "instagram",
            "scheduled_datetime": "2026-03-20T10:00:00Z",
        },
    )

    response = await client.get(
        f"{BASE_URL}/weekly",
        params={"business_profile_id": business_profile_id, "week_start": "2026-03-02"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "In week"


async def test_update_applies_partial_fields(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "title": "Original title",
            "content_type": "post",
            "platform": "instagram",
            "caption": "Original caption",
        },
    )
    item_id = create_resp.json()["id"]

    response = await client.patch(
        f"{BASE_URL}/{item_id}", json={"caption": "New caption"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["caption"] == "New caption"
    assert body["title"] == "Original title"


async def test_update_missing_returns_404(client, fake_service):
    response = await client.patch(f"{BASE_URL}/{uuid.uuid4()}", json={"caption": "x"})

    assert response.status_code == 404


async def test_delete_returns_204_and_removes_the_row(client, fake_service):
    create_resp = await client.post(
        BASE_URL,
        json={
            "business_profile_id": str(uuid.uuid4()),
            "title": "To delete",
            "content_type": "post",
            "platform": "instagram",
        },
    )
    item_id = create_resp.json()["id"]

    response = await client.delete(f"{BASE_URL}/{item_id}")

    assert response.status_code == 204
    assert uuid.UUID(item_id) not in fake_service.store


async def test_delete_missing_returns_404(client, fake_service):
    response = await client.delete(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_openapi_schema_documents_content_calendar_routes(client, fake_service):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/search" in paths
    assert f"{BASE_URL}/monthly" in paths
    assert f"{BASE_URL}/weekly" in paths
    assert f"{BASE_URL}/{{item_id}}" in paths
    assert set(paths[BASE_URL]) >= {"post", "get"}
    assert set(paths[f"{BASE_URL}/{{item_id}}"]) >= {"get", "patch", "delete"}
