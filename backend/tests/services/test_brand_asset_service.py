"""Unit tests for BrandAssetService. Both the repository and the DB session
are faked/mocked — no database connection is used or required.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.brand_asset import BrandAsset
from app.models.enums import BrandAssetStatus
from app.schemas.brand_asset import BrandAssetCreate, BrandAssetUpdate
from app.services.brand_asset import (
    BrandAssetNotFoundError,
    BrandAssetService,
    InvalidReferenceError,
)


class _FakeRepository:
    """In-memory stand-in for BrandAssetRepository."""

    def __init__(self) -> None:
        self.store: dict[uuid.UUID, BrandAsset] = {}
        self.raise_on_write: Exception | None = None

    async def create(self, brand_asset: BrandAsset) -> BrandAsset:
        if self.raise_on_write:
            raise self.raise_on_write
        brand_asset.id = brand_asset.id or uuid.uuid4()
        self.store[brand_asset.id] = brand_asset
        return brand_asset

    async def get_by_id(self, brand_asset_id: uuid.UUID) -> BrandAsset | None:
        return self.store.get(brand_asset_id)

    async def update(self, brand_asset: BrandAsset, data: dict) -> BrandAsset:
        if self.raise_on_write:
            raise self.raise_on_write
        for field, value in data.items():
            setattr(brand_asset, field, value)
        return brand_asset

    async def archive(self, brand_asset: BrandAsset) -> BrandAsset:
        brand_asset.status = BrandAssetStatus.ARCHIVED
        return brand_asset

    async def list_by_business_profile(
        self, business_profile_id, *, status=None, limit=20, offset=0
    ):
        items = [
            a
            for a in self.store.values()
            if a.business_profile_id == business_profile_id
        ]
        if status is not None:
            items = [a for a in items if a.status == status]
        return items[offset : offset + limit], len(items)


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _make_service():
    repo = _FakeRepository()
    session = AsyncMock()
    return BrandAssetService(session, repository=repo), repo, session


def _create_payload(**overrides) -> BrandAssetCreate:
    data = {"business_profile_id": uuid.uuid4(), "brand_name": "AnitaWeaves"}
    data.update(overrides)
    return BrandAssetCreate(**data)


async def test_create_persists_and_commits():
    service, repo, session = _make_service()

    result = await service.create(_create_payload())

    assert result.brand_name == "AnitaWeaves"
    assert result.id in repo.store
    session.commit.assert_awaited_once()


async def test_get_missing_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(BrandAssetNotFoundError):
        await service.get(uuid.uuid4())


async def test_get_existing_returns_asset():
    service, _repo, _session = _make_service()
    created = await service.create(_create_payload())

    fetched = await service.get(created.id)

    assert fetched is created


async def test_create_translates_invalid_business_profile_reference():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "brand_assets" violates foreign key '
        'constraint "brand_assets_business_profile_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload())


async def test_create_reraises_unrecognized_integrity_error():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error("some_other_constraint_violation")

    with pytest.raises(IntegrityError):
        await service.create(_create_payload())


async def test_update_applies_only_provided_fields():
    service, _repo, session = _make_service()
    created = await service.create(_create_payload(tagline="Handloom, reimagined"))

    updated = await service.update(created.id, BrandAssetUpdate(brand_name="Renamed"))

    assert updated.brand_name == "Renamed"
    assert updated.tagline == "Handloom, reimagined"  # untouched
    session.commit.assert_awaited()


async def test_update_missing_asset_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(BrandAssetNotFoundError):
        await service.update(uuid.uuid4(), BrandAssetUpdate(brand_name="X"))


async def test_delete_archives_instead_of_removing():
    service, repo, session = _make_service()
    created = await service.create(_create_payload())

    await service.delete(created.id)

    assert repo.store[created.id].status == BrandAssetStatus.ARCHIVED
    assert created.id in repo.store  # still present — not hard-deleted
    session.commit.assert_awaited()


async def test_delete_missing_asset_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(BrandAssetNotFoundError):
        await service.delete(uuid.uuid4())


async def test_list_filters_by_business_profile_and_status():
    service, _repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    other_business_profile_id = uuid.uuid4()
    await service.create(_create_payload(business_profile_id=business_profile_id))
    second = await service.create(
        _create_payload(business_profile_id=business_profile_id, brand_name="Draft 2")
    )
    await service.create(_create_payload(business_profile_id=other_business_profile_id))
    await service.delete(second.id)  # archives the second one

    draft_items, draft_total = await service.list(
        business_profile_id, status=BrandAssetStatus.DRAFT
    )
    all_items, all_total = await service.list(business_profile_id)

    assert draft_total == 1
    assert draft_items[0].brand_name == "AnitaWeaves"
    assert all_total == 2
