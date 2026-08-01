"""Unit tests for NotificationService. Both the repository and the DB
session are faked/mocked — no database connection is used or required.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import NotificationPriority, NotificationType
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.services.notification import (
    InvalidReferenceError,
    NotificationNotFoundError,
    NotificationService,
)


class _FakeRepository:
    """In-memory stand-in for NotificationRepository, replicating just the
    BaseRepository surface NotificationService actually calls."""

    def __init__(self) -> None:
        self.store: dict[uuid.UUID, Notification] = {}
        self.raise_on_write: Exception | None = None
        self.deleted: list[uuid.UUID] = []

    async def create(self, notification: Notification) -> Notification:
        if self.raise_on_write:
            raise self.raise_on_write
        notification.id = notification.id or uuid.uuid4()
        self.store[notification.id] = notification
        return notification

    async def get_by_id(self, notification_id: uuid.UUID) -> Notification | None:
        return self.store.get(notification_id)

    async def update(self, notification: Notification, data: dict) -> Notification:
        if self.raise_on_write:
            raise self.raise_on_write
        for field, value in data.items():
            setattr(notification, field, value)
        return notification

    async def delete(self, notification: Notification) -> None:
        self.deleted.append(notification.id)
        self.store.pop(notification.id, None)

    async def get_all(
        self, *, filters: dict | None = None, limit: int = 20, offset: int = 0
    ):
        items = list(self.store.values())
        for field, value in (filters or {}).items():
            items = [n for n in items if getattr(n, field) == value]
        return items[offset : offset + limit], len(items)


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _make_service():
    repo = _FakeRepository()
    session = AsyncMock()
    return NotificationService(session, repository=repo), repo, session


def _create_payload(**overrides) -> NotificationCreate:
    data = {
        "user_id": uuid.uuid4(),
        "notification_type": NotificationType.SYSTEM,
        "title": "Welcome to Sakhi",
    }
    data.update(overrides)
    return NotificationCreate(**data)


async def test_create_persists_and_commits():
    service, repo, session = _make_service()

    result = await service.create(_create_payload())

    assert result.title == "Welcome to Sakhi"
    assert result.id in repo.store
    session.commit.assert_awaited_once()


async def test_create_always_uses_in_app_channel():
    service, _repo, _session = _make_service()

    result = await service.create(_create_payload())

    assert result.channel.value == "in_app"


async def test_get_missing_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(NotificationNotFoundError):
        await service.get(uuid.uuid4())


async def test_get_existing_returns_notification():
    service, _repo, _session = _make_service()
    created = await service.create(_create_payload())

    fetched = await service.get(created.id)

    assert fetched is created


async def test_create_translates_invalid_user_reference():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "notifications" violates foreign key '
        'constraint "notifications_user_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload())


async def test_create_translates_invalid_business_profile_reference():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "notifications" violates foreign key '
        'constraint "notifications_business_profile_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload(business_profile_id=uuid.uuid4()))


async def test_create_reraises_unrecognized_integrity_error():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error("some_other_constraint_violation")

    with pytest.raises(IntegrityError):
        await service.create(_create_payload())


async def test_list_filters_by_user():
    service, _repo, _session = _make_service()
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    await service.create(_create_payload(user_id=user_id))
    await service.create(_create_payload(user_id=other_user_id))

    items, total = await service.list(user_id)

    assert total == 1
    assert items[0].user_id == user_id


async def test_list_filters_by_business_profile_id():
    service, _repo, _session = _make_service()
    user_id = uuid.uuid4()
    business_profile_id = uuid.uuid4()
    await service.create(
        _create_payload(user_id=user_id, business_profile_id=business_profile_id)
    )
    await service.create(_create_payload(user_id=user_id))  # no business_profile_id

    items, total = await service.list(user_id, business_profile_id=business_profile_id)

    assert total == 1
    assert items[0].business_profile_id == business_profile_id


async def test_list_filters_by_notification_type():
    service, _repo, _session = _make_service()
    user_id = uuid.uuid4()
    await service.create(
        _create_payload(
            user_id=user_id, notification_type=NotificationType.CASHFLOW_ALERT
        )
    )
    await service.create(
        _create_payload(
            user_id=user_id, notification_type=NotificationType.INVENTORY_ALERT
        )
    )

    items, total = await service.list(
        user_id, notification_type=NotificationType.INVENTORY_ALERT
    )

    assert total == 1
    assert items[0].notification_type == NotificationType.INVENTORY_ALERT


async def test_list_filters_by_status_unread_and_read():
    service, _repo, _session = _make_service()
    user_id = uuid.uuid4()
    unread = await service.create(_create_payload(user_id=user_id))
    read = await service.create(_create_payload(user_id=user_id))
    await service.mark_read(read.id)

    unread_items, unread_total = await service.list(user_id, status="unread")
    read_items, read_total = await service.list(user_id, status="read")

    assert unread_total == 1
    assert unread_items[0].id == unread.id
    assert read_total == 1
    assert read_items[0].id == read.id


async def test_mark_read_sets_is_read_and_read_at():
    service, _repo, session = _make_service()
    created = await service.create(_create_payload())

    updated = await service.mark_read(created.id)

    assert updated.is_read is True
    assert updated.read_at is not None
    session.commit.assert_awaited()


async def test_mark_read_is_idempotent():
    service, _repo, _session = _make_service()
    created = await service.create(_create_payload())

    first = await service.mark_read(created.id)
    first_read_at = first.read_at
    second = await service.mark_read(created.id)

    assert second.read_at == first_read_at


async def test_mark_read_missing_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(NotificationNotFoundError):
        await service.mark_read(uuid.uuid4())


async def test_mark_all_read_marks_every_unread_notification():
    service, _repo, session = _make_service()
    user_id = uuid.uuid4()
    first = await service.create(_create_payload(user_id=user_id))
    second = await service.create(_create_payload(user_id=user_id))

    updated_count = await service.mark_all_read(user_id)

    assert updated_count == 2
    assert first.is_read is True
    assert second.is_read is True
    session.commit.assert_awaited()


async def test_mark_all_read_only_affects_target_user():
    service, _repo, _session = _make_service()
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    mine = await service.create(_create_payload(user_id=user_id))
    someone_elses = await service.create(_create_payload(user_id=other_user_id))

    updated_count = await service.mark_all_read(user_id)

    assert updated_count == 1
    assert mine.is_read is True
    assert someone_elses.is_read is False


async def test_mark_all_read_with_nothing_unread_returns_zero():
    service, _repo, session = _make_service()
    user_id = uuid.uuid4()

    updated_count = await service.mark_all_read(user_id)

    assert updated_count == 0
    session.commit.assert_awaited()


async def test_delete_removes_the_row():
    service, repo, session = _make_service()
    created = await service.create(_create_payload())

    await service.delete(created.id)

    assert created.id not in repo.store
    assert created.id in repo.deleted
    session.commit.assert_awaited()


async def test_delete_missing_notification_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(NotificationNotFoundError):
        await service.delete(uuid.uuid4())


async def test_priority_defaults_to_normal():
    service, _repo, _session = _make_service()

    result = await service.create(_create_payload())

    assert result.priority == NotificationPriority.NORMAL
