"""Endpoint-level tests for Marketing Studio.

MarketingContentAnalysisService is replaced via FastAPI's
dependency_overrides with an in-memory fake, same pattern as
tests/api/test_inventory_router.py — no real AI provider or database call
happens.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest

from app.api.deps import get_current_app_user
from app.api.v1.endpoints import marketing_studio as endpoint_module
from app.main import app
from app.models.enums import MarketingAnalysisSourceType
from app.models.marketing_content_analysis import MarketingContentAnalysis
from app.services.marketing_content_analysis import (
    BusinessProfileOrBrandNotFoundError,
    MarketingAnalysisNotFoundError,
    ReelBriefRequiredError,
)


class _FakeUser:
    id = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def _fake_current_user() -> _FakeUser:
    return _FakeUser()

BASE_URL = "/api/v1/marketing-studio"

_SAMPLE_ANALYSIS = {
    "virality_score": 72.5,
    "virality_reasoning": "Engagement rate is well above average for this niche.",
    "product_detection": ["Rose-Pista Tart"],
    "comment_themes": ["praise"],
    "comment_summary": "Mostly positive.",
    "audience_sentiment": {
        "positive_pct": 70,
        "neutral_pct": 20,
        "negative_pct": 10,
        "summary": "Largely positive.",
    },
    "hook_analysis": {"rating": "Strong", "feedback": "Opens with a visual payoff."},
    "cta_analysis": {"rating": "Weak", "feedback": "No explicit CTA."},
    "caption_analysis": {"rating": "Average", "feedback": "Descriptive but no urgency."},
    "thumbnail_analysis": None,
    "recommendations": ["Add a clear CTA"],
    "ai_captions": ["Caption A"],
    "next_reel_ideas": ["Behind the scenes"],
    "performance_summary": "A strong post held back by a missing CTA.",
}

_SAMPLE_BRIEF = {
    "concept": "Behind the scenes",
    "hook": "POV: you just walked in.",
    "script_beats": ["Show the ingredients"],
    "shot_list": ["Close-up of hands"],
    "caption": "Every tart, hand-piped.",
    "hashtags": ["homebakery"],
    "cta": "DM to order",
}


class _FakeService:
    def __init__(self) -> None:
        self.store: dict[uuid.UUID, MarketingContentAnalysis] = {}
        self.raise_not_found = False

    def _make_row(self, business_profile_id, *, analysis=None, reel_brief=None, **kwargs):
        now = datetime.now(timezone.utc)
        row = MarketingContentAnalysis(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            business_profile_id=business_profile_id,
            social_connection_id=kwargs.get("social_connection_id"),
            source_type=kwargs.get("source_type", MarketingAnalysisSourceType.MANUAL),
            source_url=kwargs.get("source_url"),
            caption=kwargs.get("caption"),
            hashtags=kwargs.get("hashtags") or [],
            comments_sample=kwargs.get("comments_sample") or [],
            metrics=kwargs.get("metrics") or {},
            analysis=analysis,
            reel_brief=reel_brief,
        )
        self.store[row.id] = row
        return row

    async def analyze(self, *, user_id, business_profile_id, **kwargs):
        if self.raise_not_found:
            raise BusinessProfileOrBrandNotFoundError("Business profile not found.")
        metrics = kwargs.get("metrics")
        return self._make_row(
            business_profile_id,
            analysis=_SAMPLE_ANALYSIS,
            source_type=kwargs.get("source_type", MarketingAnalysisSourceType.MANUAL),
            source_url=kwargs.get("source_url"),
            caption=kwargs.get("caption"),
            hashtags=kwargs.get("hashtags"),
            comments_sample=kwargs.get("comments_sample"),
            metrics=metrics.model_dump(mode="json") if metrics else {},
        )

    async def generate_reel(self, *, user_id, business_profile_id, angle):
        if self.raise_not_found:
            raise BusinessProfileOrBrandNotFoundError("Business profile not found.")
        return self._make_row(business_profile_id, reel_brief=_SAMPLE_BRIEF)

    async def list(self, business_profile_id, *, limit=20, offset=0):
        items = [r for r in self.store.values() if r.business_profile_id == business_profile_id]
        return items[offset : offset + limit], len(items)

    async def get(self, analysis_id):
        row = self.store.get(analysis_id)
        if row is None:
            raise MarketingAnalysisNotFoundError(str(analysis_id))
        return row

    async def generate_visual(self, *, analysis_id, user_id):
        row = self.store.get(analysis_id)
        if row is None:
            raise MarketingAnalysisNotFoundError(str(analysis_id))
        if not row.reel_brief:
            raise ReelBriefRequiredError("This analysis has no reel brief yet.")
        row.reel_brief = {**row.reel_brief, "image_url": "data:image/png;base64,ZmFrZQ=="}
        return row

    async def generate_video(self, *, analysis_id, user_id):
        row = self.store.get(analysis_id)
        if row is None:
            raise MarketingAnalysisNotFoundError(str(analysis_id))
        if not row.reel_brief:
            raise ReelBriefRequiredError("This analysis has no reel brief yet.")
        row.reel_brief = {**row.reel_brief, "video_url": "https://fal.media/files/fake.mp4"}
        return row


@pytest.fixture
async def fake_service() -> AsyncGenerator[_FakeService, None]:
    service = _FakeService()
    app.dependency_overrides[endpoint_module.get_service] = lambda: service
    app.dependency_overrides[get_current_app_user] = _fake_current_user
    try:
        yield service
    finally:
        app.dependency_overrides.pop(endpoint_module.get_service, None)
        app.dependency_overrides.pop(get_current_app_user, None)


async def test_analyze_manual_returns_201_with_analysis(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    response = await client.post(
        BASE_URL + "/analyze",
        data={
            "business_profile_id": business_profile_id,
            "source_type": "manual",
            "caption": "Our new tart!",
            "hashtags": "bakery, tart",
            "comments_sample": "Looks amazing\nWhen is this available",
            "views": "1000",
            "likes": "80",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["business_profile_id"] == business_profile_id
    assert body["analysis"]["virality_score"] == 72.5
    assert body["engagement_rate"] == 8.0


async def test_analyze_missing_business_profile_returns_404(client, fake_service):
    fake_service.raise_not_found = True
    response = await client.post(
        BASE_URL + "/analyze",
        data={"business_profile_id": str(uuid.uuid4()), "source_type": "manual"},
    )
    assert response.status_code == 404


async def test_generate_reel_returns_201_with_brief(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    response = await client.post(
        BASE_URL + "/generate-reel",
        json={"business_profile_id": business_profile_id, "angle": "Diwali"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["reel_brief"]["concept"] == "Behind the scenes"
    assert body["analysis"] is None


async def test_list_returns_only_matching_business(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    other_id = str(uuid.uuid4())
    await client.post(
        BASE_URL + "/generate-reel", json={"business_profile_id": business_profile_id}
    )
    fake_service.raise_not_found = False
    await client.post(BASE_URL + "/generate-reel", json={"business_profile_id": other_id})

    response = await client.get(BASE_URL, params={"business_profile_id": business_profile_id})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1


async def test_get_missing_analysis_returns_404(client, fake_service):
    response = await client.get(f"{BASE_URL}/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_get_existing_analysis_returns_200(client, fake_service):
    business_profile_id = str(uuid.uuid4())
    create_resp = await client.post(
        BASE_URL + "/generate-reel", json={"business_profile_id": business_profile_id}
    )
    analysis_id = create_resp.json()["id"]

    response = await client.get(f"{BASE_URL}/{analysis_id}")
    assert response.status_code == 200
    assert response.json()["id"] == analysis_id


async def test_generate_visual_returns_200_with_image_url(client, fake_service):
    create_resp = await client.post(
        BASE_URL + "/generate-reel", json={"business_profile_id": str(uuid.uuid4())}
    )
    analysis_id = create_resp.json()["id"]

    response = await client.post(f"{BASE_URL}/{analysis_id}/generate-visual")
    assert response.status_code == 200
    assert response.json()["reel_brief"]["image_url"] == "data:image/png;base64,ZmFrZQ=="


async def test_generate_visual_missing_analysis_returns_404(client, fake_service):
    response = await client.post(f"{BASE_URL}/{uuid.uuid4()}/generate-visual")
    assert response.status_code == 404


async def test_generate_video_returns_200_with_video_url(client, fake_service):
    create_resp = await client.post(
        BASE_URL + "/generate-reel", json={"business_profile_id": str(uuid.uuid4())}
    )
    analysis_id = create_resp.json()["id"]

    response = await client.post(f"{BASE_URL}/{analysis_id}/generate-video")
    assert response.status_code == 200
    assert response.json()["reel_brief"]["video_url"] == "https://fal.media/files/fake.mp4"


async def test_generate_video_missing_analysis_returns_404(client, fake_service):
    response = await client.post(f"{BASE_URL}/{uuid.uuid4()}/generate-video")
    assert response.status_code == 404
