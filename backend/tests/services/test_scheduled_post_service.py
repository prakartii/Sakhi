"""Unit tests for ScheduledPostService. All three repositories and the DB
session are faked/mocked — no database connection is used or required.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.content_calendar_item import ContentCalendarItem
from app.models.enums import (
    ContentType,
    PublishingStatus,
    SocialConnectionStatus,
    SocialMediaPlatform,
)
from app.models.scheduled_post import ScheduledPost
from app.models.social_media_connection import SocialMediaConnection
from app.schemas.scheduled_post import ScheduledPostCreate, UpdateStatusRequest
from app.services.scheduled_post import (
    InvalidContentCalendarReferenceError,
    InvalidReferenceError,
    InvalidScheduleError,
    InvalidSocialConnectionError,
    InvalidStatusTransitionError,
    ScheduledPostNotFoundError,
    ScheduledPostService,
)

_FUTURE = datetime.now(timezone.utc) + timedelta(days=1)
_PAST = datetime.now(timezone.utc) - timedelta(days=1)


class _FakeRepository:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, ScheduledPost] = {}
        self.raise_on_write: Exception | None = None
        self.deleted: list[uuid.UUID] = []

    async def create(self, post: ScheduledPost) -> ScheduledPost:
        if self.raise_on_write:
            raise self.raise_on_write
        post.id = post.id or uuid.uuid4()
        post.retry_count = post.retry_count or 0
        self.store[post.id] = post
        return post

    async def get_by_id(self, post_id: uuid.UUID) -> ScheduledPost | None:
        return self.store.get(post_id)

    async def update(self, post: ScheduledPost, data: dict) -> ScheduledPost:
        if self.raise_on_write:
            raise self.raise_on_write
        for field, value in data.items():
            setattr(post, field, value)
        return post

    async def delete(self, post: ScheduledPost) -> None:
        self.deleted.append(post.id)
        self.store.pop(post.id, None)

    async def list_by_business_profile(
        self, business_profile_id, *, publishing_status=None, limit=20, offset=0
    ):
        items = [
            p
            for p in self.store.values()
            if p.business_profile_id == business_profile_id
        ]
        if publishing_status is not None:
            items = [p for p in items if p.publishing_status == publishing_status]
        return items[offset : offset + limit], len(items)

    async def list_queue(self, business_profile_id, *, limit=20, offset=0):
        queue_statuses = {PublishingStatus.QUEUED, PublishingStatus.PUBLISHING}
        items = [
            p
            for p in self.store.values()
            if p.business_profile_id == business_profile_id
            and p.publishing_status in queue_statuses
        ]
        return items[offset : offset + limit], len(items)

    async def list_history(
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


class _FakeContentRepository:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, ContentCalendarItem] = {}

    async def get_by_id(self, item_id):
        return self.store.get(item_id)


class _FakeConnectionRepository:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, SocialMediaConnection] = {}

    async def get_by_id(self, connection_id):
        return self.store.get(connection_id)


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _content_item(
    *, business_profile_id, platform=SocialMediaPlatform.INSTAGRAM
) -> ContentCalendarItem:
    return ContentCalendarItem(
        id=uuid.uuid4(),
        business_profile_id=business_profile_id,
        title="Diwali teaser",
        content_type=ContentType.POST,
        platform=platform,
    )


def _connection(
    *,
    business_profile_id,
    platform=SocialMediaPlatform.INSTAGRAM,
    connection_status=SocialConnectionStatus.CONNECTED,
) -> SocialMediaConnection:
    return SocialMediaConnection(
        id=uuid.uuid4(),
        business_profile_id=business_profile_id,
        platform=platform,
        connection_status=connection_status,
    )


def _make_service():
    repo = _FakeRepository()
    content_repo = _FakeContentRepository()
    connection_repo = _FakeConnectionRepository()
    session = AsyncMock()
    service = ScheduledPostService(
        session,
        repository=repo,
        content_calendar_repository=content_repo,
        connection_repository=connection_repo,
    )
    return service, repo, content_repo, connection_repo, session


def _valid_setup(service, content_repo, connection_repo):
    business_profile_id = uuid.uuid4()
    content_item = _content_item(business_profile_id=business_profile_id)
    connection = _connection(business_profile_id=business_profile_id)
    content_repo.store[content_item.id] = content_item
    connection_repo.store[connection.id] = connection
    return business_profile_id, content_item, connection


def _create_payload(**overrides) -> ScheduledPostCreate:
    data = {
        "business_profile_id": uuid.uuid4(),
        "content_calendar_id": uuid.uuid4(),
        "social_connection_id": uuid.uuid4(),
        "scheduled_time": _FUTURE,
    }
    data.update(overrides)
    return ScheduledPostCreate(**data)


async def test_schedule_post_persists_and_commits():
    service, repo, content_repo, connection_repo, session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )

    result = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )

    assert result.id in repo.store
    assert result.publishing_status == PublishingStatus.QUEUED
    session.commit.assert_awaited_once()


async def test_schedule_post_rejects_past_scheduled_time():
    service, _repo, _content_repo, _connection_repo, _session = _make_service()

    with pytest.raises(InvalidScheduleError):
        await service.schedule_post(_create_payload(scheduled_time=_PAST))


async def test_schedule_post_rejects_missing_content_calendar_item():
    service, _repo, _content_repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    connection = _connection(business_profile_id=business_profile_id)
    connection_repo.store[connection.id] = connection

    with pytest.raises(InvalidContentCalendarReferenceError):
        await service.schedule_post(
            _create_payload(
                business_profile_id=business_profile_id,
                social_connection_id=connection.id,
            )
        )


async def test_schedule_post_rejects_content_item_from_different_business():
    service, _repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    content_item = _content_item(business_profile_id=uuid.uuid4())  # different business
    connection = _connection(business_profile_id=business_profile_id)
    content_repo.store[content_item.id] = content_item
    connection_repo.store[connection.id] = connection

    with pytest.raises(InvalidContentCalendarReferenceError):
        await service.schedule_post(
            _create_payload(
                business_profile_id=business_profile_id,
                content_calendar_id=content_item.id,
                social_connection_id=connection.id,
            )
        )


async def test_schedule_post_rejects_missing_social_connection():
    service, _repo, content_repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    content_item = _content_item(business_profile_id=business_profile_id)
    content_repo.store[content_item.id] = content_item

    with pytest.raises(InvalidSocialConnectionError):
        await service.schedule_post(
            _create_payload(
                business_profile_id=business_profile_id,
                content_calendar_id=content_item.id,
            )
        )


async def test_schedule_post_rejects_social_connection_from_different_business():
    service, _repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    content_item = _content_item(business_profile_id=business_profile_id)
    connection = _connection(business_profile_id=uuid.uuid4())  # different business
    content_repo.store[content_item.id] = content_item
    connection_repo.store[connection.id] = connection

    with pytest.raises(InvalidSocialConnectionError):
        await service.schedule_post(
            _create_payload(
                business_profile_id=business_profile_id,
                content_calendar_id=content_item.id,
                social_connection_id=connection.id,
            )
        )


async def test_schedule_post_rejects_social_connection_wrong_platform():
    service, _repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    content_item = _content_item(
        business_profile_id=business_profile_id, platform=SocialMediaPlatform.INSTAGRAM
    )
    connection = _connection(
        business_profile_id=business_profile_id, platform=SocialMediaPlatform.LINKEDIN
    )
    content_repo.store[content_item.id] = content_item
    connection_repo.store[connection.id] = connection

    with pytest.raises(InvalidSocialConnectionError):
        await service.schedule_post(
            _create_payload(
                business_profile_id=business_profile_id,
                content_calendar_id=content_item.id,
                social_connection_id=connection.id,
            )
        )


async def test_schedule_post_rejects_disconnected_social_connection():
    service, _repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    content_item = _content_item(business_profile_id=business_profile_id)
    connection = _connection(
        business_profile_id=business_profile_id,
        connection_status=SocialConnectionStatus.DISCONNECTED,
    )
    content_repo.store[content_item.id] = content_item
    connection_repo.store[connection.id] = connection

    with pytest.raises(InvalidSocialConnectionError):
        await service.schedule_post(
            _create_payload(
                business_profile_id=business_profile_id,
                content_calendar_id=content_item.id,
                social_connection_id=connection.id,
            )
        )


async def test_schedule_post_translates_invalid_business_profile_reference():
    service, repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    repo.raise_on_write = _integrity_error(
        'insert or update on table "scheduled_posts" violates foreign key '
        'constraint "scheduled_posts_business_profile_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.schedule_post(
            _create_payload(
                business_profile_id=business_profile_id,
                content_calendar_id=content_item.id,
                social_connection_id=connection.id,
            )
        )


async def test_schedule_post_reraises_unrecognized_integrity_error():
    service, repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    repo.raise_on_write = _integrity_error("some_other_constraint_violation")

    with pytest.raises(IntegrityError):
        await service.schedule_post(
            _create_payload(
                business_profile_id=business_profile_id,
                content_calendar_id=content_item.id,
                social_connection_id=connection.id,
            )
        )


async def test_get_missing_raises_not_found():
    service, _repo, _content_repo, _connection_repo, _session = _make_service()

    with pytest.raises(ScheduledPostNotFoundError):
        await service.get(uuid.uuid4())


async def test_get_existing_returns_post():
    service, _repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )

    fetched = await service.get(created.id)

    assert fetched is created


async def test_get_queue_returns_only_queued_and_publishing():
    service, repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    queued = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    published = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    await repo.update(published, {"publishing_status": PublishingStatus.PUBLISHED})

    items, total = await service.get_queue(business_profile_id)

    assert total == 1
    assert items[0].id == queued.id


async def test_publishing_history_defaults_to_resolved_statuses():
    service, repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    queued = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    published = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    await repo.update(published, {"publishing_status": PublishingStatus.PUBLISHED})

    items, total = await service.publishing_history(business_profile_id)

    assert total == 1
    assert items[0].id == published.id
    assert queued.id not in [item.id for item in items]


async def test_publishing_history_filters_to_one_status():
    service, repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    published = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    failed = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    await repo.update(published, {"publishing_status": PublishingStatus.PUBLISHED})
    await repo.update(failed, {"publishing_status": PublishingStatus.FAILED})

    items, total = await service.publishing_history(
        business_profile_id, publishing_status=PublishingStatus.FAILED
    )

    assert total == 1
    assert items[0].id == failed.id


async def test_cancel_schedule_sets_cancelled():
    service, _repo, content_repo, connection_repo, session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )

    result = await service.cancel_schedule(created.id)

    assert result.publishing_status == PublishingStatus.CANCELLED
    session.commit.assert_awaited()


async def test_cancel_schedule_is_idempotent_when_already_cancelled():
    service, _repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    await service.cancel_schedule(created.id)

    result = await service.cancel_schedule(created.id)

    assert result.publishing_status == PublishingStatus.CANCELLED


async def test_cancel_schedule_rejects_already_published():
    service, repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    await repo.update(created, {"publishing_status": PublishingStatus.PUBLISHED})

    with pytest.raises(InvalidStatusTransitionError):
        await service.cancel_schedule(created.id)


async def test_cancel_schedule_missing_raises_not_found():
    service, _repo, _content_repo, _connection_repo, _session = _make_service()

    with pytest.raises(ScheduledPostNotFoundError):
        await service.cancel_schedule(uuid.uuid4())


async def test_retry_failed_post_requeues_and_increments_retry_count():
    service, repo, content_repo, connection_repo, session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    await repo.update(
        created, {"publishing_status": PublishingStatus.FAILED, "error_log": "timeout"}
    )

    result = await service.retry_failed_post(created.id)

    assert result.publishing_status == PublishingStatus.QUEUED
    assert result.retry_count == 1
    assert result.error_log == "timeout"  # preserved, not cleared
    session.commit.assert_awaited()


async def test_retry_failed_post_rejects_non_failed_status():
    service, _repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )

    with pytest.raises(InvalidStatusTransitionError):
        await service.retry_failed_post(created.id)


async def test_retry_failed_post_missing_raises_not_found():
    service, _repo, _content_repo, _connection_repo, _session = _make_service()

    with pytest.raises(ScheduledPostNotFoundError):
        await service.retry_failed_post(uuid.uuid4())


async def test_update_status_sets_published_at_when_published():
    service, _repo, content_repo, connection_repo, session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )

    result = await service.update_status(
        created.id,
        UpdateStatusRequest(
            publishing_status=PublishingStatus.PUBLISHED,
            published_url="https://instagram.com/p/xyz",
        ),
    )

    assert result.publishing_status == PublishingStatus.PUBLISHED
    assert result.published_url == "https://instagram.com/p/xyz"
    assert result.published_at is not None
    session.commit.assert_awaited()


async def test_update_status_does_not_set_published_at_when_failed():
    service, _repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )

    result = await service.update_status(
        created.id,
        UpdateStatusRequest(
            publishing_status=PublishingStatus.FAILED, error_log="Rate limited"
        ),
    )

    assert result.publishing_status == PublishingStatus.FAILED
    assert result.published_at is None
    assert result.error_log == "Rate limited"


async def test_update_status_replaces_fields_not_merges():
    service, repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    await repo.update(created, {"error_log": "first failure"})

    result = await service.update_status(
        created.id, UpdateStatusRequest(publishing_status=PublishingStatus.FAILED)
    )

    assert result.error_log is None  # replaced, not merged with the prior value


async def test_update_status_rejects_when_already_published():
    service, repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    await repo.update(created, {"publishing_status": PublishingStatus.PUBLISHED})

    with pytest.raises(InvalidStatusTransitionError):
        await service.update_status(
            created.id, UpdateStatusRequest(publishing_status=PublishingStatus.FAILED)
        )


async def test_update_status_rejects_when_already_cancelled():
    service, repo, content_repo, connection_repo, _session = _make_service()
    business_profile_id, content_item, connection = _valid_setup(
        service, content_repo, connection_repo
    )
    created = await service.schedule_post(
        _create_payload(
            business_profile_id=business_profile_id,
            content_calendar_id=content_item.id,
            social_connection_id=connection.id,
        )
    )
    await service.cancel_schedule(created.id)

    with pytest.raises(InvalidStatusTransitionError):
        await service.update_status(
            created.id,
            UpdateStatusRequest(publishing_status=PublishingStatus.PUBLISHING),
        )


async def test_update_status_missing_raises_not_found():
    service, _repo, _content_repo, _connection_repo, _session = _make_service()

    with pytest.raises(ScheduledPostNotFoundError):
        await service.update_status(
            uuid.uuid4(), UpdateStatusRequest(publishing_status=PublishingStatus.FAILED)
        )
