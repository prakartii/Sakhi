"""Unit tests for ContentCalendarItemService. The repositories and the DB
session are all faked/mocked — no database connection is used or required.
"""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.content_calendar_item import ContentCalendarItem
from app.models.enums import ContentStatus, ContentType, SocialMediaPlatform
from app.models.social_media_connection import SocialMediaConnection
from app.schemas.content_calendar_item import (
    ContentCalendarItemCreate,
    ContentCalendarItemUpdate,
)
from app.services.content_calendar_item import (
    ContentCalendarItemNotFoundError,
    ContentCalendarItemService,
    InvalidReferenceError,
    InvalidSocialConnectionError,
)


class _FakeRepository:
    """In-memory stand-in for ContentCalendarItemRepository."""

    def __init__(self) -> None:
        self.store: dict[uuid.UUID, ContentCalendarItem] = {}
        self.raise_on_write: Exception | None = None
        self.deleted: list[uuid.UUID] = []

    async def create(self, item: ContentCalendarItem) -> ContentCalendarItem:
        if self.raise_on_write:
            raise self.raise_on_write
        item.id = item.id or uuid.uuid4()
        self.store[item.id] = item
        return item

    async def get_by_id(self, item_id: uuid.UUID) -> ContentCalendarItem | None:
        return self.store.get(item_id)

    async def update(
        self, item: ContentCalendarItem, data: dict
    ) -> ContentCalendarItem:
        if self.raise_on_write:
            raise self.raise_on_write
        for field, value in data.items():
            setattr(item, field, value)
        return item

    async def delete(self, item: ContentCalendarItem) -> None:
        self.deleted.append(item.id)
        self.store.pop(item.id, None)

    async def list_by_business_profile(
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

    async def list_by_date_range(
        self,
        business_profile_id,
        *,
        start,
        end,
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
            and start <= i.scheduled_datetime < end
        ]
        if platform is not None:
            items = [i for i in items if i.platform == platform]
        if status is not None:
            items = [i for i in items if i.status == status]
        items.sort(key=lambda i: i.scheduled_datetime)
        return items[offset : offset + limit], len(items)

    async def search(self, query, *, business_profile_id=None, limit=20, offset=0):
        items = list(self.store.values())
        if business_profile_id is not None:
            items = [i for i in items if i.business_profile_id == business_profile_id]
        needle = query.lower()
        items = [
            i
            for i in items
            if needle in (i.title or "").lower() or needle in (i.caption or "").lower()
        ]
        return items[offset : offset + limit], len(items)


class _FakeConnectionRepository:
    """In-memory stand-in for SocialMediaConnectionRepository — only
    get_by_id is exercised by ContentCalendarItemService."""

    def __init__(self) -> None:
        self.store: dict[uuid.UUID, SocialMediaConnection] = {}

    async def get_by_id(self, connection_id):
        return self.store.get(connection_id)


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _make_service():
    repo = _FakeRepository()
    connection_repo = _FakeConnectionRepository()
    session = AsyncMock()
    service = ContentCalendarItemService(
        session, repository=repo, connection_repository=connection_repo
    )
    return service, repo, connection_repo, session


def _create_payload(**overrides) -> ContentCalendarItemCreate:
    data = {
        "business_profile_id": uuid.uuid4(),
        "title": "Diwali collection teaser",
        "content_type": ContentType.POST,
        "platform": SocialMediaPlatform.INSTAGRAM,
    }
    data.update(overrides)
    return ContentCalendarItemCreate(**data)


def _connection(
    *, business_profile_id, platform=SocialMediaPlatform.INSTAGRAM
) -> SocialMediaConnection:
    return SocialMediaConnection(
        id=uuid.uuid4(), business_profile_id=business_profile_id, platform=platform
    )


async def test_create_persists_and_commits():
    service, repo, _connection_repo, session = _make_service()

    result = await service.create(_create_payload())

    assert result.id in repo.store
    assert result.status == ContentStatus.DRAFT
    session.commit.assert_awaited_once()


async def test_create_translates_invalid_business_profile_reference():
    service, repo, _connection_repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "content_calendar_items" violates foreign '
        'key constraint "content_calendar_items_business_profile_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload())


async def test_create_reraises_unrecognized_integrity_error():
    service, repo, _connection_repo, _session = _make_service()
    repo.raise_on_write = _integrity_error("some_other_constraint_violation")

    with pytest.raises(IntegrityError):
        await service.create(_create_payload())


async def test_create_with_valid_social_connection_succeeds():
    service, _repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    connection = _connection(business_profile_id=business_profile_id)
    connection_repo.store[connection.id] = connection

    result = await service.create(
        _create_payload(
            business_profile_id=business_profile_id, social_connection_id=connection.id
        )
    )

    assert result.social_connection_id == connection.id


async def test_create_with_missing_social_connection_raises():
    service, _repo, _connection_repo, _session = _make_service()

    with pytest.raises(InvalidSocialConnectionError):
        await service.create(_create_payload(social_connection_id=uuid.uuid4()))


async def test_create_with_social_connection_from_different_business_raises():
    service, _repo, connection_repo, _session = _make_service()
    connection = _connection(business_profile_id=uuid.uuid4())
    connection_repo.store[connection.id] = connection

    with pytest.raises(InvalidSocialConnectionError):
        await service.create(
            _create_payload(
                business_profile_id=uuid.uuid4(),  # different from connection's
                social_connection_id=connection.id,
            )
        )


async def test_create_with_social_connection_wrong_platform_raises():
    service, _repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    connection = _connection(
        business_profile_id=business_profile_id, platform=SocialMediaPlatform.LINKEDIN
    )
    connection_repo.store[connection.id] = connection

    with pytest.raises(InvalidSocialConnectionError):
        await service.create(
            _create_payload(
                business_profile_id=business_profile_id,
                platform=SocialMediaPlatform.INSTAGRAM,
                social_connection_id=connection.id,
            )
        )


async def test_get_missing_raises_not_found():
    service, _repo, _connection_repo, _session = _make_service()

    with pytest.raises(ContentCalendarItemNotFoundError):
        await service.get(uuid.uuid4())


async def test_get_existing_returns_item():
    service, _repo, _connection_repo, _session = _make_service()
    created = await service.create(_create_payload())

    fetched = await service.get(created.id)

    assert fetched is created


async def test_list_filters_by_business_profile_and_platform():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            platform=SocialMediaPlatform.INSTAGRAM,
        )
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            platform=SocialMediaPlatform.PINTEREST,
        )
    )
    await service.create(_create_payload())  # different business

    items, total = await service.list(
        business_profile_id, platform=SocialMediaPlatform.PINTEREST
    )

    assert total == 1
    assert items[0].platform == SocialMediaPlatform.PINTEREST


async def test_list_filters_by_status():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id, status=ContentStatus.DRAFT
        )
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id, status=ContentStatus.SCHEDULED
        )
    )

    items, total = await service.list(
        business_profile_id, status=ContentStatus.SCHEDULED
    )

    assert total == 1
    assert items[0].status == ContentStatus.SCHEDULED


async def test_monthly_calendar_includes_only_items_in_that_month():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    in_month = await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            scheduled_datetime=datetime(2026, 3, 15, tzinfo=timezone.utc),
        )
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            scheduled_datetime=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
    )
    await service.create(
        _create_payload(business_profile_id=business_profile_id)  # unscheduled
    )

    items, total = await service.monthly_calendar(
        business_profile_id, year=2026, month=3
    )

    assert total == 1
    assert items[0].id == in_month.id


async def test_monthly_calendar_december_rolls_into_next_year_boundary():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    december_item = await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            scheduled_datetime=datetime(2026, 12, 31, 23, 0, tzinfo=timezone.utc),
        )
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            scheduled_datetime=datetime(2027, 1, 1, 0, 0, tzinfo=timezone.utc),
        )
    )

    items, total = await service.monthly_calendar(
        business_profile_id, year=2026, month=12
    )

    assert total == 1
    assert items[0].id == december_item.id


async def test_weekly_calendar_includes_only_items_in_that_week():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    in_week = await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            scheduled_datetime=datetime(2026, 3, 4, tzinfo=timezone.utc),
        )
    )
    await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            scheduled_datetime=datetime(2026, 3, 9, tzinfo=timezone.utc),
        )
    )

    items, total = await service.weekly_calendar(
        business_profile_id, week_start=date(2026, 3, 2)
    )

    assert total == 1
    assert items[0].id == in_week.id


async def test_search_matches_title_or_caption():
    service, _repo, _connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    await service.create(
        _create_payload(business_profile_id=business_profile_id, title="Diwali teaser")
    )
    await service.create(
        _create_payload(business_profile_id=business_profile_id, title="New arrivals")
    )

    items, total = await service.search(
        "diwali", business_profile_id=business_profile_id
    )

    assert total == 1
    assert items[0].title == "Diwali teaser"


async def test_update_applies_only_provided_fields():
    service, _repo, _connection_repo, session = _make_service()
    created = await service.create(_create_payload(caption="Original"))

    updated = await service.update(
        created.id, ContentCalendarItemUpdate(caption="Updated")
    )

    assert updated.caption == "Updated"
    assert updated.title == "Diwali collection teaser"  # untouched
    session.commit.assert_awaited()


async def test_update_missing_item_raises_not_found():
    service, _repo, _connection_repo, _session = _make_service()

    with pytest.raises(ContentCalendarItemNotFoundError):
        await service.update(uuid.uuid4(), ContentCalendarItemUpdate(caption="x"))


async def test_update_validates_new_social_connection_against_current_platform():
    service, _repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    created = await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            platform=SocialMediaPlatform.INSTAGRAM,
        )
    )
    wrong_platform_connection = _connection(
        business_profile_id=business_profile_id, platform=SocialMediaPlatform.FACEBOOK
    )
    connection_repo.store[wrong_platform_connection.id] = wrong_platform_connection

    with pytest.raises(InvalidSocialConnectionError):
        await service.update(
            created.id,
            ContentCalendarItemUpdate(
                social_connection_id=wrong_platform_connection.id
            ),
        )


async def test_update_allows_valid_social_connection():
    service, _repo, connection_repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    created = await service.create(
        _create_payload(
            business_profile_id=business_profile_id,
            platform=SocialMediaPlatform.INSTAGRAM,
        )
    )
    connection = _connection(
        business_profile_id=business_profile_id, platform=SocialMediaPlatform.INSTAGRAM
    )
    connection_repo.store[connection.id] = connection

    updated = await service.update(
        created.id, ContentCalendarItemUpdate(social_connection_id=connection.id)
    )

    assert updated.social_connection_id == connection.id


async def test_delete_removes_the_row():
    service, repo, _connection_repo, session = _make_service()
    created = await service.create(_create_payload())

    await service.delete(created.id)

    assert created.id not in repo.store
    assert created.id in repo.deleted
    session.commit.assert_awaited()


async def test_delete_missing_item_raises_not_found():
    service, _repo, _connection_repo, _session = _make_service()

    with pytest.raises(ContentCalendarItemNotFoundError):
        await service.delete(uuid.uuid4())
