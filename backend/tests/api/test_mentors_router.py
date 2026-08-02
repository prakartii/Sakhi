"""Endpoint-level tests for GET /mentors/matches.

Same isolation pattern as tests/api/test_schemes_router.py: repositories
replaced via dependency_overrides, app.ai.explanations.explain
monkeypatched on the endpoint module so no real AI provider call happens.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest

from app.ai.explanations import Explanation
from app.api.deps import get_business_profile_repository, get_mentor_repository
from app.api.v1.endpoints import mentors as endpoint_module
from app.main import app
from app.models.business_profile import BusinessProfile
from app.models.enums import BusinessRegistrationType, MentorAvailability
from app.models.mentor_profile import MentorProfile

BASE_URL = "/api/v1/mentors"


class _FakeProfileRepo:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, BusinessProfile] = {}

    async def get_by_id(self, profile_id):
        return self.store.get(profile_id)


class _FakeMentorRepo:
    def __init__(self) -> None:
        self.mentors: list[MentorProfile] = []

    async def list_active(self, *, availability_status=None, limit=20, offset=0):
        items = self.mentors
        if availability_status is not None:
            items = [m for m in items if m.availability_status == availability_status]
        return items[offset : offset + limit], len(items)


async def _fake_explain(request):
    return Explanation(why=f"Why: {request.subject}", basis="Based on your profile.")


@pytest.fixture
async def fakes(monkeypatch) -> AsyncGenerator[tuple[_FakeProfileRepo, _FakeMentorRepo], None]:
    profile_repo = _FakeProfileRepo()
    mentor_repo = _FakeMentorRepo()
    monkeypatch.setattr(endpoint_module, "explain", _fake_explain)
    app.dependency_overrides[get_business_profile_repository] = lambda: profile_repo
    app.dependency_overrides[get_mentor_repository] = lambda: mentor_repo
    try:
        yield profile_repo, mentor_repo
    finally:
        app.dependency_overrides.pop(get_business_profile_repository, None)
        app.dependency_overrides.pop(get_mentor_repository, None)


def _make_profile(**overrides) -> BusinessProfile:
    defaults = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        business_name="Bagru Block Prints",
        registration_type=BusinessRegistrationType.SOLE_PROPRIETORSHIP,
        industry="Textiles",
        business_category="Block printing",
        country="India",
    )
    defaults.update(overrides)
    return BusinessProfile(**defaults)


def _make_mentor(**overrides) -> MentorProfile:
    defaults = dict(
        id=uuid.uuid4(),
        full_name="Shabnam Qureshi",
        bio="Block-print exporter with 14 years of experience.",
        expertise_areas=["Textiles", "Exports"],
        industry_focus="Textiles",
        years_experience=14,
        avatar_url=None,
        availability_status=MentorAvailability.AVAILABLE,
        is_active=True,
    )
    defaults.update(overrides)
    return MentorProfile(**defaults)


async def test_matches_missing_business_profile_returns_404(client, fakes):
    response = await client.get(BASE_URL + "/matches", params={"business_profile_id": str(uuid.uuid4())})
    assert response.status_code == 404


async def test_matches_empty_directory_returns_empty_list_not_error(client, fakes):
    profile_repo, _mentor_repo = fakes
    profile = _make_profile()
    profile_repo.store[profile.id] = profile

    response = await client.get(BASE_URL + "/matches", params={"business_profile_id": str(profile.id)})

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_matches_available_and_expertise_matched_scores_highest(client, fakes):
    profile_repo, mentor_repo = fakes
    profile = _make_profile(industry="Textiles", business_category="Block printing")
    profile_repo.store[profile.id] = profile
    mentor_repo.mentors = [
        _make_mentor(full_name="Shabnam Qureshi", expertise_areas=["Textiles"]),
        _make_mentor(
            full_name="Unavailable Umang",
            expertise_areas=["Textiles"],
            availability_status=MentorAvailability.UNAVAILABLE,
        ),
    ]

    response = await client.get(BASE_URL + "/matches", params={"business_profile_id": str(profile.id)})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["items"][0]["full_name"] == "Shabnam Qureshi"
    assert body["items"][0]["is_eligible"] is True
    assert body["items"][1]["full_name"] == "Unavailable Umang"
    assert body["items"][1]["is_eligible"] is False
    assert body["items"][0]["why"]
    assert body["items"][0]["basis"]
