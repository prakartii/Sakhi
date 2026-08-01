"""Unit tests for BusinessProfileService. Both the repository and the DB
session are faked/mocked — no database connection is used or required.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.business_profile import BusinessProfile
from app.models.enums import BusinessStage, BusinessStatus
from app.schemas.business_profile import (
    BusinessProfileCreate,
    BusinessProfilePut,
    BusinessProfileUpdate,
)
from app.services.business_profile import (
    BusinessProfileConflictError,
    BusinessProfileNotFoundError,
    BusinessProfileService,
    InvalidReferenceError,
)


class _FakeRepository:
    """In-memory stand-in for BusinessProfileRepository."""

    def __init__(self) -> None:
        self.store: dict[uuid.UUID, BusinessProfile] = {}
        self.raise_on_write: Exception | None = None

    async def create(self, business_profile: BusinessProfile) -> BusinessProfile:
        if self.raise_on_write:
            raise self.raise_on_write
        business_profile.id = business_profile.id or uuid.uuid4()
        self.store[business_profile.id] = business_profile
        return business_profile

    async def get_by_id(self, business_profile_id: uuid.UUID) -> BusinessProfile | None:
        return self.store.get(business_profile_id)

    async def update(
        self, business_profile: BusinessProfile, data: dict
    ) -> BusinessProfile:
        if self.raise_on_write:
            raise self.raise_on_write
        for field, value in data.items():
            setattr(business_profile, field, value)
        return business_profile

    async def archive(self, business_profile: BusinessProfile) -> BusinessProfile:
        business_profile.status = BusinessStatus.ARCHIVED
        return business_profile

    async def list_by_user(self, user_id, *, status=None, limit=20, offset=0):
        items = [bp for bp in self.store.values() if bp.user_id == user_id]
        if status is not None:
            items = [bp for bp in items if bp.status == status]
        return items[offset : offset + limit], len(items)


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _make_service():
    repo = _FakeRepository()
    session = AsyncMock()
    return BusinessProfileService(session, repository=repo), repo, session


def _create_payload(**overrides) -> BusinessProfileCreate:
    data = {"user_id": uuid.uuid4(), "business_name": "Meera Tailoring"}
    data.update(overrides)
    return BusinessProfileCreate(**data)


async def test_create_persists_and_commits():
    service, repo, session = _make_service()

    result = await service.create(_create_payload())

    assert result.business_name == "Meera Tailoring"
    assert result.id in repo.store
    session.commit.assert_awaited_once()


async def test_get_missing_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(BusinessProfileNotFoundError):
        await service.get(uuid.uuid4())


async def test_get_existing_returns_profile():
    service, _repo, _session = _make_service()
    created = await service.create(_create_payload())

    fetched = await service.get(created.id)

    assert fetched is created


async def test_create_translates_primary_conflict_and_rolls_back():
    service, repo, session = _make_service()
    repo.raise_on_write = _integrity_error(
        "duplicate key value violates unique constraint "
        '"uq_business_profiles_primary_per_user"'
    )

    with pytest.raises(BusinessProfileConflictError):
        await service.create(_create_payload())

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


async def test_create_translates_invalid_user_reference():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "business_profiles" violates foreign key '
        'constraint "business_profiles_user_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.create(_create_payload())


async def test_create_translates_invalid_language_reference():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "business_profiles" violates foreign key '
        'constraint "business_profiles_preferred_language_id_fkey"'
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
    created = await service.create(_create_payload(city="Pune"))

    updated = await service.update(
        created.id, BusinessProfileUpdate(business_name="Renamed")
    )

    assert updated.business_name == "Renamed"
    assert updated.city == "Pune"  # untouched
    session.commit.assert_awaited()


async def test_update_missing_profile_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(BusinessProfileNotFoundError):
        await service.update(uuid.uuid4(), BusinessProfileUpdate(business_name="X"))


async def test_delete_archives_instead_of_removing():
    service, repo, session = _make_service()
    created = await service.create(_create_payload())

    await service.delete(created.id)

    assert repo.store[created.id].status == BusinessStatus.ARCHIVED
    assert created.id in repo.store  # still present — not hard-deleted
    session.commit.assert_awaited()


async def test_delete_missing_profile_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(BusinessProfileNotFoundError):
        await service.delete(uuid.uuid4())


async def test_list_filters_by_user_and_status():
    service, _repo, _session = _make_service()
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    await service.create(_create_payload(user_id=user_id, business_name="A"))
    second = await service.create(
        _create_payload(user_id=user_id, business_name="B", is_primary=False)
    )
    await service.create(_create_payload(user_id=other_user_id, business_name="C"))
    await service.delete(second.id)  # archives B

    active_items, active_total = await service.list(
        user_id, status=BusinessStatus.ACTIVE
    )
    all_items, all_total = await service.list(user_id)

    assert active_total == 1
    assert active_items[0].business_name == "A"
    assert all_total == 2


# -- replace() (PUT) ----------------------------------------------------------


async def test_replace_resets_fields_omitted_from_the_payload():
    service, _repo, session = _make_service()
    created = await service.create(_create_payload(city="Pune", owner_name="Meera"))

    replaced = await service.replace(
        created.id, BusinessProfilePut(business_name="Meera Tailoring")
    )

    assert replaced.city is None
    assert replaced.owner_name is None
    session.commit.assert_awaited()


async def test_replace_applies_all_provided_fields():
    service, _repo, _session = _make_service()
    created = await service.create(_create_payload())

    replaced = await service.replace(
        created.id,
        BusinessProfilePut(
            business_name="Meera Tailoring",
            owner_name="Meera Iyer",
            business_stage=BusinessStage.GROWING,
        ),
    )

    assert replaced.owner_name == "Meera Iyer"
    assert replaced.business_stage == BusinessStage.GROWING


async def test_replace_missing_profile_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(BusinessProfileNotFoundError):
        await service.replace(uuid.uuid4(), BusinessProfilePut(business_name="X"))


# -- get_onboarding_status() ---------------------------------------------------


async def test_onboarding_status_reports_missing_fields():
    service, _repo, _session = _make_service()
    created = await service.create(_create_payload(owner_name="Meera"))

    onboarding = await service.get_onboarding_status(created.id)

    assert onboarding.is_complete is False
    assert "owner_name" in onboarding.completed_fields
    assert "business_description" in onboarding.missing_fields
    assert 0 < onboarding.completion_percentage < 100


async def test_onboarding_status_complete_when_all_required_fields_set():
    service, _repo, _session = _make_service()
    created = await service.create(
        _create_payload(
            owner_name="Meera Iyer",
            business_category="Tailoring",
            business_description="Custom tailoring for working women.",
            target_audience="Working women, 25-45",
            products_or_services="Alterations, custom stitching",
            business_stage=BusinessStage.STARTUP,
            city="Pune",
            state="Maharashtra",
            # country already defaults to "India" from BusinessProfileCreate
        )
    )

    onboarding = await service.get_onboarding_status(created.id)

    assert onboarding.is_complete is True
    assert onboarding.missing_fields == []
    assert onboarding.completion_percentage == 100.0


async def test_onboarding_status_missing_profile_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(BusinessProfileNotFoundError):
        await service.get_onboarding_status(uuid.uuid4())
