"""Unit tests for WebsiteService. Both repositories and the DB session are
faked/mocked — no database connection is used or required.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import WebsiteStatus
from app.models.website import Website
from app.models.website_version import WebsiteVersion
from app.schemas.website import WebsiteCreate, WebsiteUpdate
from app.services.website import (
    InvalidReferenceError,
    WebsiteConflictError,
    WebsiteNotFoundError,
    WebsiteService,
    WebsiteVersionNotFoundError,
)


class _FakeWebsiteRepository:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, Website] = {}
        self.raise_on_write: Exception | None = None

    async def create(self, website: Website) -> Website:
        if self.raise_on_write:
            raise self.raise_on_write
        website.id = website.id or uuid.uuid4()
        self.store[website.id] = website
        return website

    async def get_by_id(self, website_id: uuid.UUID) -> Website | None:
        return self.store.get(website_id)

    async def update(self, website: Website, data: dict) -> Website:
        if self.raise_on_write:
            raise self.raise_on_write
        for field, value in data.items():
            setattr(website, field, value)
        return website

    async def archive(self, website: Website) -> Website:
        website.status = WebsiteStatus.ARCHIVED
        return website

    async def list_by_business_profile(
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


class _FakeVersionRepository:
    def __init__(self) -> None:
        self.store: list[WebsiteVersion] = []

    async def create(self, version: WebsiteVersion) -> WebsiteVersion:
        version.id = version.id or uuid.uuid4()
        self.store.append(version)
        return version

    async def count(self, filters: dict) -> int:
        website_id = filters["website_id"]
        return len([v for v in self.store if v.website_id == website_id])

    async def list_by_website(self, website_id, *, limit=20, offset=0):
        items = sorted(
            (v for v in self.store if v.website_id == website_id),
            key=lambda v: v.version_number,
            reverse=True,
        )
        return items[offset : offset + limit], len(items)

    async def get_by_website_and_version(self, website_id, version_number):
        for v in self.store:
            if v.website_id == website_id and v.version_number == version_number:
                return v
        return None


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _make_service():
    repo = _FakeWebsiteRepository()
    version_repo = _FakeVersionRepository()
    session = AsyncMock()
    service = WebsiteService(session, repository=repo, version_repository=version_repo)
    return service, repo, version_repo, session


def _create_payload(**overrides) -> WebsiteCreate:
    data = {"business_profile_id": uuid.uuid4(), "website_name": "AnitaWeaves Store"}
    data.update(overrides)
    return WebsiteCreate(**data)


async def test_create_persists_and_commits():
    service, repo, _versions, session = _make_service()

    result = await service.create(_create_payload())

    assert result.website_name == "AnitaWeaves Store"
    assert result.id in repo.store
    session.commit.assert_awaited_once()


async def test_create_records_version_1():
    service, _repo, versions, _session = _make_service()

    website = await service.create(_create_payload())

    assert len(versions.store) == 1
    assert versions.store[0].version_number == 1
    assert versions.store[0].website_id == website.id
    assert versions.store[0].website_name == "AnitaWeaves Store"
    assert versions.store[0].change_notes == "Initial version"


async def test_get_missing_raises_not_found():
    service, _repo, _versions, _session = _make_service()

    with pytest.raises(WebsiteNotFoundError):
        await service.get(uuid.uuid4())


async def test_create_translates_custom_domain_conflict():
    service, repo, _versions, session = _make_service()
    repo.raise_on_write = _integrity_error(
        'duplicate key value violates unique constraint "uq_websites_custom_domain"'
    )

    with pytest.raises(WebsiteConflictError):
        await service.create(_create_payload(custom_domain="shop.example.com"))
    session.rollback.assert_awaited_once()


async def test_create_translates_invalid_business_profile_reference():
    service, repo, _versions, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "websites" violates foreign key '
        'constraint "websites_business_profile_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload())


async def test_update_applies_fields_and_records_a_new_version():
    service, _repo, versions, session = _make_service()
    website = await service.create(_create_payload())

    updated = await service.update(
        website.id,
        WebsiteUpdate(website_name="Renamed Store", change_notes="Rebranded homepage"),
    )

    assert updated.website_name == "Renamed Store"
    assert len(versions.store) == 2
    latest = versions.store[-1]
    assert latest.version_number == 2
    assert latest.website_name == "Renamed Store"
    assert latest.change_notes == "Rebranded homepage"
    session.commit.assert_awaited()


async def test_update_missing_website_raises_not_found():
    service, _repo, _versions, _session = _make_service()

    with pytest.raises(WebsiteNotFoundError):
        await service.update(uuid.uuid4(), WebsiteUpdate(website_name="X"))


async def test_delete_archives_and_records_final_version():
    service, repo, versions, session = _make_service()
    website = await service.create(_create_payload())

    await service.delete(website.id)

    assert repo.store[website.id].status == WebsiteStatus.ARCHIVED
    assert website.id in repo.store  # still present — not hard-deleted
    assert len(versions.store) == 2
    assert versions.store[-1].status == WebsiteStatus.ARCHIVED
    assert versions.store[-1].change_notes == "Archived"
    session.commit.assert_awaited()


async def test_delete_missing_website_raises_not_found():
    service, _repo, _versions, _session = _make_service()

    with pytest.raises(WebsiteNotFoundError):
        await service.delete(uuid.uuid4())


async def test_list_filters_by_business_profile_and_status():
    service, _repo, _versions, _session = _make_service()
    business_profile_id = uuid.uuid4()
    other_business_profile_id = uuid.uuid4()
    await service.create(_create_payload(business_profile_id=business_profile_id))
    second = await service.create(
        _create_payload(business_profile_id=business_profile_id, website_name="Site 2")
    )
    await service.create(_create_payload(business_profile_id=other_business_profile_id))
    await service.delete(second.id)  # archives the second one

    draft_items, draft_total = await service.list(
        business_profile_id, status=WebsiteStatus.DRAFT
    )
    all_items, all_total = await service.list(business_profile_id)

    assert draft_total == 1
    assert draft_items[0].website_name == "AnitaWeaves Store"
    assert all_total == 2


async def test_list_versions_returns_newest_first():
    service, _repo, _versions, _session = _make_service()
    website = await service.create(_create_payload())
    await service.update(website.id, WebsiteUpdate(website_name="v2"))
    await service.update(website.id, WebsiteUpdate(website_name="v3"))

    items, total = await service.list_versions(website.id)

    assert total == 3
    assert [v.version_number for v in items] == [3, 2, 1]


async def test_list_versions_missing_website_raises_not_found():
    service, _repo, _versions, _session = _make_service()

    with pytest.raises(WebsiteNotFoundError):
        await service.list_versions(uuid.uuid4())


async def test_get_version_returns_the_requested_snapshot():
    service, _repo, _versions, _session = _make_service()
    website = await service.create(_create_payload())
    await service.update(website.id, WebsiteUpdate(website_name="Renamed"))

    version = await service.get_version(website.id, 2)

    assert version.website_name == "Renamed"
    assert version.version_number == 2


async def test_get_version_missing_version_raises_not_found():
    service, _repo, _versions, _session = _make_service()
    website = await service.create(_create_payload())

    with pytest.raises(WebsiteVersionNotFoundError):
        await service.get_version(website.id, 99)


async def test_get_version_missing_website_raises_not_found():
    service, _repo, _versions, _session = _make_service()

    with pytest.raises(WebsiteNotFoundError):
        await service.get_version(uuid.uuid4(), 1)
