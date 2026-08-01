"""Endpoint-level tests for the Scheduled Posts API.

ScheduledPostService is replaced via FastAPI's dependency_overrides with an
in-memory fake, so these tests exercise routing, status codes and response
shapes without a live database. Uses the shared `client` fixture from
tests/conftest.py (an in-process ASGI client against the real app).
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

import pytest

from app.api.v1.endpoints import scheduled_posts as endpoint_module
from app.main import app
from app.models.enums import PublishingStatus
from app.models.scheduled_post import ScheduledPost
from app.services.scheduled_post import (
    InvalidContentCalendarReferenceError,
    InvalidScheduleError,
    InvalidSocialConnectionError,
    InvalidStatusTransitionError,
    ScheduledPostNotFoundError,
)

BASE_URL = "/api/v1/scheduled-posts"
_FUTURE_ISO = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, ScheduledPost] = {}
        self.raise_on_schedule: Exception | None = None

    async def schedule_post(self, payload):
        if self.raise_on_schedule:
            raise self.raise_on_schedule
        now = datetime.now(timezone.utc)
        post = ScheduledPost(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            publishing_status=PublishingStatus.QUEUED,
            retry_count=0,
            published_url=None,
            provider_response=None,
            error_log=None,
            published_at=None,
            **payload.model_dump(),
        )
        self.store[post.id] = post
        return post

    async def get(self, post_id):
        post = self.store.get(post_id)
        if post is None:
            raise ScheduledPostNotFoundError(str(post_id))
        return post

    async def get_queue(self, business_profile_id, *, limit=20, offset=0):
        queue_statuses = {PublishingStatus.QUEUED, PublishingStatus.PUBLISHING}
        items = [
            p
            for p in self.store.values()
            if p.business_profile_id == business_profile_id
            and p.publishing_status in queue_statuses
        ]
        return items[offset : offset + limit], len(items)

    async def publishing_history(
        self, business_profile_id, *, publishing_status=None, limit=20, offset=0
    ):
        history_statuses = {
            PublishingStatus.PUBLISHED,
            PublishingStatus.FAILED,
            PublishingStatus.CANCELLED,
        }
        statuses = (
            {publishing_status} if publishing_status is not None else history_statuses
        )
        items = [
            p
            for p in self.store.values()
            if p.business_profile_id == business_profile_id
            and p.publishing_status in statuses
        ]
        return items[offset : offset + limit], len(items)

    async def cancel_schedule(self, post_id):
        post = await self.get(post_id)
        if post.publishing_status == PublishingStatus.PUBLISHED:
            raise InvalidStatusTransitionError("cannot cancel a published post.")
        post.publishing_status = PublishingStatus.CANCELLED
        return post

    async def retry_failed_post(self, post_id):
        post = await self.get(post_id)
        if post.publishing_status != PublishingStatus.FAILED:
            raise InvalidStatusTransitionError("only a failed post can be retried.")
        post.publishing_status = PublishingStatus.QUEUED
        post.retry_count += 1
        return post

    async def update_status(self, post_id, payload):
        post = await self.get(post_id)
        if post.publishing_status in (
            PublishingStatus.PUBLISHED,
            PublishingStatus.CANCELLED,
        ):
            raise InvalidStatusTransitionError("terminal state.")
        post.publishing_status = payload.publishing_status
        post.published_url = payload.published_url
        post.provider_response = payload.provider_response
        post.error_log = payload.error_log
        if payload.publishing_status == PublishingStatus.PUBLISHED:
            post.published_at = datetime.now(timezone.utc)
        return post


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)


def _schedule_payload(**overrides) -> dict:
    data = {
        "business_profile_id": str(uuid.uuid4()),
        "content_calendar_id": str(uuid.uuid4()),
        "social_connection_id": str(uuid.uuid4()),
        "scheduled_time": _FUTURE_ISO,
    }
    data.update(overrides)
    return data


async def test_schedule_post_returns_201_with_created_post(client, fake_service):
    response = await client.post(BASE_URL, json=_schedule_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["publishing_status"] == "queued"
    assert body["retry_count"] == 0
    assert "id" in body and "created_at" in body


async def test_schedule_post_missing_required_field_returns_422(client, fake_service):
    payload = _schedule_payload()
    del payload["content_calendar_id"]

    response = await client.post(BASE_URL, json=payload)

    assert response.status_code == 422


async def test_schedule_post_invalid_content_reference_returns_422(
    client, fake_service
):
    fake_service.raise_on_schedule = InvalidContentCalendarReferenceError(
        "content_calendar_id does not reference an existing content calendar item."
    )

    response = await client.post(BASE_URL, json=_schedule_payload())

    assert response.status_code == 422


async def test_schedule_post_invalid_social_connection_returns_422(
    client, fake_service
):
    fake_service.raise_on_schedule = InvalidSocialConnectionError(
        "social_connection_id is not currently connected."
    )

    response = await client.post(BASE_URL, json=_schedule_payload())

    assert response.status_code == 422


async def test_schedule_post_invalid_schedule_returns_422(client, fake_service):
    fake_service.raise_on_schedule = InvalidScheduleError(
        "scheduled_time must be in the future."
    )

    response = await client.post(BASE_URL, json=_schedule_payload())

    assert response.status_code == 422


async def test_get_missing_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_existing_returns_200(client, fake_service):
    create_resp = await client.post(BASE_URL, json=_schedule_payload())
    post_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{post_id}")

    assert response.status_code == 200
    assert response.json()["id"] == post_id


async def test_get_queue_without_business_profile_id_returns_422(client, fake_service):
    response = await client.get(f"{BASE_URL}/queue")

    assert response.status_code == 422


async def test_get_queue_returns_only_pending_posts(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    create_resp = await client.post(
        BASE_URL, json=_schedule_payload(business_profile_id=business_profile_id)
    )
    other_resp = await client.post(
        BASE_URL, json=_schedule_payload(business_profile_id=business_profile_id)
    )
    await client.post(f"{BASE_URL}/{other_resp.json()['id']}/cancel")

    response = await client.get(
        f"{BASE_URL}/queue", params={"business_profile_id": business_profile_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == create_resp.json()["id"]


async def test_publishing_history_returns_resolved_outcomes(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    queued_resp = await client.post(
        BASE_URL, json=_schedule_payload(business_profile_id=business_profile_id)
    )
    cancelled_resp = await client.post(
        BASE_URL, json=_schedule_payload(business_profile_id=business_profile_id)
    )
    await client.post(f"{BASE_URL}/{cancelled_resp.json()['id']}/cancel")

    response = await client.get(
        f"{BASE_URL}/history", params={"business_profile_id": business_profile_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == cancelled_resp.json()["id"]
    assert queued_resp.json()["id"] not in [item["id"] for item in body["items"]]


async def test_cancel_schedule_sets_cancelled_status(client, fake_service):
    create_resp = await client.post(BASE_URL, json=_schedule_payload())
    post_id = create_resp.json()["id"]

    response = await client.post(f"{BASE_URL}/{post_id}/cancel")

    assert response.status_code == 200
    assert response.json()["publishing_status"] == "cancelled"


async def test_cancel_schedule_missing_returns_404(client, fake_service):
    response = await client.post(f"{BASE_URL}/{uuid.uuid4()}/cancel")

    assert response.status_code == 404


async def test_retry_failed_post_rejects_non_failed_post(client, fake_service):
    create_resp = await client.post(BASE_URL, json=_schedule_payload())
    post_id = create_resp.json()["id"]

    response = await client.post(f"{BASE_URL}/{post_id}/retry")

    assert response.status_code == 422


async def test_retry_failed_post_missing_returns_404(client, fake_service):
    response = await client.post(f"{BASE_URL}/{uuid.uuid4()}/retry")

    assert response.status_code == 404


async def test_update_status_to_published_sets_published_at(client, fake_service):
    create_resp = await client.post(BASE_URL, json=_schedule_payload())
    post_id = create_resp.json()["id"]

    response = await client.patch(
        f"{BASE_URL}/{post_id}/status",
        json={
            "publishing_status": "published",
            "published_url": "https://instagram.com/p/xyz",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["publishing_status"] == "published"
    assert body["published_url"] == "https://instagram.com/p/xyz"
    assert body["published_at"] is not None


async def test_update_status_missing_returns_404(client, fake_service):
    response = await client.patch(
        f"{BASE_URL}/{uuid.uuid4()}/status", json={"publishing_status": "failed"}
    )

    assert response.status_code == 404


async def test_update_status_invalid_status_returns_422(client, fake_service):
    create_resp = await client.post(BASE_URL, json=_schedule_payload())
    post_id = create_resp.json()["id"]

    response = await client.patch(
        f"{BASE_URL}/{post_id}/status", json={"publishing_status": "uploading"}
    )

    assert response.status_code == 422


async def test_openapi_schema_documents_scheduled_posts_routes(client, fake_service):
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert BASE_URL in paths
    assert f"{BASE_URL}/queue" in paths
    assert f"{BASE_URL}/history" in paths
    assert f"{BASE_URL}/{{scheduled_post_id}}" in paths
    assert f"{BASE_URL}/{{scheduled_post_id}}/cancel" in paths
    assert f"{BASE_URL}/{{scheduled_post_id}}/retry" in paths
    assert f"{BASE_URL}/{{scheduled_post_id}}/status" in paths
