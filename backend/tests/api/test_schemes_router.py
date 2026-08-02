"""Endpoint-level tests for GET /schemes/matches.

BusinessProfileRepository and GovernmentSchemeRepository are replaced via
FastAPI's dependency_overrides with in-memory fakes, and
app.ai.explanations.explain is monkeypatched on the endpoint module so no
real AI provider call happens — same isolation pattern as
tests/api/test_inventory_router.py, adapted for this module's read-only,
compute-on-read shape.
"""

import uuid
from collections.abc import AsyncGenerator

import pytest

from app.ai.explanations import Explanation
from app.api.deps import get_business_profile_repository, get_government_scheme_repository
from app.api.v1.endpoints import schemes as endpoint_module
from app.main import app
from app.models.business_profile import BusinessProfile
from app.models.enums import BusinessRegistrationType, SchemeLevel

BASE_URL = "/api/v1/schemes"


class _FakeProfileRepo:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, BusinessProfile] = {}

    async def get_by_id(self, profile_id):
        return self.store.get(profile_id)


class _FakeSchemeRepo:
    def __init__(self) -> None:
        self.schemes: list = []

    async def list_active(self, *, limit=20, offset=0):
        return self.schemes[offset : offset + limit], len(self.schemes)


async def _fake_explain(request):
    return Explanation(why=f"Why: {request.subject}", basis="Based on your profile.")


@pytest.fixture
async def fakes(monkeypatch) -> AsyncGenerator[tuple[_FakeProfileRepo, _FakeSchemeRepo], None]:
    profile_repo = _FakeProfileRepo()
    scheme_repo = _FakeSchemeRepo()
    monkeypatch.setattr(endpoint_module, "explain", _fake_explain)
    app.dependency_overrides[get_business_profile_repository] = lambda: profile_repo
    app.dependency_overrides[get_government_scheme_repository] = lambda: scheme_repo
    try:
        yield profile_repo, scheme_repo
    finally:
        app.dependency_overrides.pop(get_business_profile_repository, None)
        app.dependency_overrides.pop(get_government_scheme_repository, None)


def _make_profile(**overrides) -> BusinessProfile:
    defaults = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        business_name="Bagru Block Prints",
        registration_type=BusinessRegistrationType.SOLE_PROPRIETORSHIP,
        udyam_registration_number="UDYAM-RJ-17-004339",
        year_established=2022,
        state="Rajasthan",
        country="India",
    )
    defaults.update(overrides)
    return BusinessProfile(**defaults)


def _make_scheme(**overrides):
    from app.models.government_scheme import GovernmentScheme

    defaults = dict(
        id=uuid.uuid4(),
        scheme_name="PM Vishwakarma",
        scheme_code="PM-VISHWAKARMA",
        description="Support for artisans.",
        issuing_authority="Ministry of MSME",
        scheme_level=SchemeLevel.CENTRAL,
        eligibility_criteria={
            "criteria": [
                {
                    "field": "has_udyam_registration",
                    "operator": "eq",
                    "value": True,
                    "weight": 1,
                    "required": True,
                    "label": "Business is Udyam-registered",
                }
            ]
        },
        benefits="Rs 15,000 toolkit incentive.",
        application_url="https://pmvishwakarma.gov.in",
        category="craft & artisan",
        min_business_age_months=None,
        applicable_states=None,
        is_active=True,
    )
    defaults.update(overrides)
    return GovernmentScheme(**defaults)


async def test_matches_missing_business_profile_returns_404(client, fakes):
    response = await client.get(BASE_URL + "/matches", params={"business_profile_id": str(uuid.uuid4())})
    assert response.status_code == 404


async def test_matches_missing_business_profile_id_returns_422(client, fakes):
    response = await client.get(BASE_URL + "/matches")
    assert response.status_code == 422


async def test_matches_ranks_eligible_scheme_highest(client, fakes):
    profile_repo, scheme_repo = fakes
    profile = _make_profile()
    profile_repo.store[profile.id] = profile
    scheme_repo.schemes = [
        _make_scheme(scheme_name="PM Vishwakarma"),
        _make_scheme(
            scheme_name="Never Eligible",
            scheme_code="NEVER",
            eligibility_criteria={
                "criteria": [
                    {
                        "field": "registration_type",
                        "operator": "eq",
                        "value": "public_limited",
                        "weight": 1,
                        "required": True,
                        "label": "Registered as a public limited company",
                    }
                ]
            },
        ),
    ]

    response = await client.get(BASE_URL + "/matches", params={"business_profile_id": str(profile.id)})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["items"][0]["scheme_name"] == "PM Vishwakarma"
    assert body["items"][0]["is_eligible"] is True
    assert body["items"][0]["match_score"] == 100.0
    assert body["items"][1]["scheme_name"] == "Never Eligible"
    assert body["items"][1]["is_eligible"] is False
    assert body["items"][0]["why"]
    assert body["items"][0]["basis"]


async def test_matches_respects_top_n(client, fakes):
    profile_repo, scheme_repo = fakes
    profile = _make_profile()
    profile_repo.store[profile.id] = profile
    scheme_repo.schemes = [_make_scheme(scheme_code=f"S{i}", scheme_name=f"Scheme {i}") for i in range(5)]

    response = await client.get(
        BASE_URL + "/matches",
        params={"business_profile_id": str(profile.id), "top_n": 2},
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 2


async def test_matches_empty_catalog_returns_empty_list(client, fakes):
    profile_repo, _scheme_repo = fakes
    profile = _make_profile()
    profile_repo.store[profile.id] = profile

    response = await client.get(BASE_URL + "/matches", params={"business_profile_id": str(profile.id)})

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
