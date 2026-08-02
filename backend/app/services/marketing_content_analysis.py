"""Business logic for Marketing Studio.

Owns the transaction boundary around each use case: fetch the owning
profile + its brand kit, run the AI analysis/generation, persist the
result, and — the "continuously update Sakhi's Business Intelligence
layer" part of the spec — write a short business_memory note so future
Advisor/Content Calendar calls can recall what worked (or didn't) via the
same embeddings retrieval every other memory already goes through. That
last step is best-effort: an embeddings hiccup degrades to "the analysis
is saved but not yet recallable by search," never to losing the analysis
itself.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.memory_embedding import embed_memory_content
from app.ai.embeddings.persist import save_embedded_chunks
from app.ai.image import generate_image, get_nano_banana_provider
from app.ai.marketing import (
    ContentAnalysis,
    ContentMetrics,
    ReelBrief,
    analyze_content,
    describe_thumbnail,
    generate_reel_brief,
)
from app.ai.providers.base import AIProviderError
from app.ai.video import generate_video
from app.models.brand_asset import BrandAsset
from app.models.business_memory import BusinessMemory
from app.models.business_profile import BusinessProfile
from app.models.enums import MarketingAnalysisSourceType, MemorySource, MemoryType
from app.models.marketing_content_analysis import MarketingContentAnalysis
from app.repositories.brand_asset import BrandAssetRepository
from app.repositories.business_memory import BusinessMemoryRepository
from app.repositories.business_profile import BusinessProfileRepository
from app.repositories.marketing_content_analysis import MarketingContentAnalysisRepository
from app.services.ai_mapping import to_ai_brand_kit, to_ai_business_profile

_PAST_LEARNINGS_LIMIT = 5


class BusinessProfileOrBrandNotFoundError(Exception):
    """No business profile with that id, not owned by the caller, or it
    has no brand kit yet."""


class MarketingAnalysisNotFoundError(Exception):
    """No marketing_content_analyses row exists for the given id."""


class ReelBriefRequiredError(Exception):
    """generate_visual()/generate_video() need a reel_brief (hook/concept)
    to build a prompt from — this analysis row doesn't have one yet."""


class MarketingContentAnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._analyses = MarketingContentAnalysisRepository(session)
        self._profiles = BusinessProfileRepository(session)
        self._brands = BrandAssetRepository(session)
        self._memories = BusinessMemoryRepository(session)

    async def _get_owned_profile_and_brand(
        self, business_profile_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[BusinessProfile, BrandAsset]:
        profile = await self._profiles.get_by_id(business_profile_id)
        if profile is None or profile.user_id != user_id:
            raise BusinessProfileOrBrandNotFoundError("Business profile not found.")
        brands, _ = await self._brands.list_by_business_profile(profile.id, limit=1)
        if not brands:
            raise BusinessProfileOrBrandNotFoundError(
                "No brand kit exists for this business yet — complete onboarding first."
            )
        return profile, brands[0]

    async def analyze(
        self,
        *,
        user_id: uuid.UUID,
        business_profile_id: uuid.UUID,
        social_connection_id: uuid.UUID | None,
        source_type: MarketingAnalysisSourceType,
        source_url: str | None,
        caption: str | None,
        hashtags: list[str],
        comments_sample: list[str],
        metrics: ContentMetrics,
        thumbnail_data_url: str | None,
    ) -> MarketingContentAnalysis:
        profile, brand = await self._get_owned_profile_and_brand(business_profile_id, user_id)

        thumbnail_description: str | None = None
        if thumbnail_data_url is not None:
            try:
                thumbnail_description = await describe_thumbnail(thumbnail_data_url)
            except AIProviderError:
                # Vision is best-effort — analysis still proceeds on
                # caption/metrics/comments alone, just without
                # thumbnail_analysis in the result.
                thumbnail_description = None

        analysis: ContentAnalysis = await analyze_content(
            to_ai_business_profile(profile),
            to_ai_brand_kit(brand),
            caption=caption,
            hashtags=hashtags,
            metrics=metrics,
            comments_sample=comments_sample,
            thumbnail_description=thumbnail_description,
        )

        row = MarketingContentAnalysis(
            business_profile_id=profile.id,
            social_connection_id=social_connection_id,
            source_type=source_type,
            source_url=source_url,
            caption=caption,
            hashtags=hashtags,
            comments_sample=comments_sample,
            metrics=metrics.model_dump(mode="json"),
            analysis=analysis.model_dump(mode="json"),
        )
        await self._analyses.create(row)
        await self._remember(profile.id, analysis)
        await self._session.commit()
        return row

    async def generate_reel(
        self,
        *,
        user_id: uuid.UUID,
        business_profile_id: uuid.UUID,
        angle: str | None,
    ) -> MarketingContentAnalysis:
        profile, brand = await self._get_owned_profile_and_brand(business_profile_id, user_id)

        past, _ = await self._analyses.list_by_business_profile(
            profile.id, limit=_PAST_LEARNINGS_LIMIT
        )
        past_learnings = [
            f"{a.analysis['virality_score']}/100 — {a.analysis['performance_summary']}"
            for a in past
            if a.analysis
        ]

        brief: ReelBrief = await generate_reel_brief(
            to_ai_business_profile(profile),
            to_ai_brand_kit(brand),
            angle=angle,
            past_learnings=past_learnings,
        )

        row = MarketingContentAnalysis(
            business_profile_id=profile.id,
            source_type=MarketingAnalysisSourceType.MANUAL,
            reel_brief=brief.model_dump(mode="json"),
        )
        await self._analyses.create(row)
        await self._session.commit()
        return row

    async def _get_owned_analysis(
        self, analysis_id: uuid.UUID, user_id: uuid.UUID
    ) -> MarketingContentAnalysis:
        row = await self._analyses.get_by_id(analysis_id)
        if row is None:
            raise MarketingAnalysisNotFoundError(str(analysis_id))
        # Ownership runs through the analysis's own business profile, not a
        # direct column on this row — same indirection used everywhere else
        # (content_generation.py, business_memory) rather than duplicating
        # a user_id column here.
        await self._get_owned_profile_and_brand(row.business_profile_id, user_id)
        return row

    @staticmethod
    def _reel_brief_prompt(row: MarketingContentAnalysis) -> str | None:
        brief = row.reel_brief or {}
        return brief.get("hook") or brief.get("concept")

    async def generate_visual(
        self, *, analysis_id: uuid.UUID, user_id: uuid.UUID
    ) -> MarketingContentAnalysis:
        """Nano Banana (Gemini, free tier) — a cover visual for this reel
        brief's hook/concept. Additive: never called automatically by
        generate_reel()."""
        row = await self._get_owned_analysis(analysis_id, user_id)
        prompt = self._reel_brief_prompt(row)
        if not prompt:
            raise ReelBriefRequiredError(
                "This analysis has no reel brief yet — generate one first."
            )

        image = await generate_image(prompt, "post", "square", provider=get_nano_banana_provider())
        brief = dict(row.reel_brief or {})
        brief["image_url"] = image.url
        await self._analyses.update(row, {"reel_brief": brief})
        await self._session.commit()
        return row

    async def generate_video(
        self, *, analysis_id: uuid.UUID, user_id: uuid.UUID
    ) -> MarketingContentAnalysis:
        """fal.ai — a real, billed generation for this reel brief's hook/
        concept. Additive and deliberately never automatic, same reasoning
        as app.ai.video's module docstring."""
        row = await self._get_owned_analysis(analysis_id, user_id)
        prompt = self._reel_brief_prompt(row)
        if not prompt:
            raise ReelBriefRequiredError(
                "This analysis has no reel brief yet — generate one first."
            )

        video = await generate_video(prompt)
        brief = dict(row.reel_brief or {})
        brief["video_url"] = video.url
        await self._analyses.update(row, {"reel_brief": brief})
        await self._session.commit()
        return row

    async def list(
        self, business_profile_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[MarketingContentAnalysis], int]:
        return await self._analyses.list_by_business_profile(
            business_profile_id, limit=limit, offset=offset
        )

    async def get(self, analysis_id: uuid.UUID) -> MarketingContentAnalysis:
        row = await self._analyses.get_by_id(analysis_id)
        if row is None:
            raise MarketingAnalysisNotFoundError(str(analysis_id))
        return row

    async def _remember(self, business_profile_id: uuid.UUID, analysis: ContentAnalysis) -> None:
        """The 'Business Intelligence layer' update: one short, embedded
        memory per analysis so future Advisor/Content Calendar calls can
        recall it via semantic search, same as any other business_memory
        row — see app.ai.embeddings.retrieve."""
        content = (
            f"Marketing Studio: a piece of content scored {analysis.virality_score}/100 "
            f"({analysis.virality_reasoning}). {analysis.performance_summary}"
        )
        memory = BusinessMemory(
            business_profile_id=business_profile_id,
            memory_type=MemoryType.FACT,
            title="Marketing Studio analysis",
            content=content,
            source=MemorySource.AI_INFERRED,
            importance_score=min(5, max(1, round(analysis.virality_score / 20))),
        )
        await self._memories.create(memory)
        await self._session.flush()
        try:
            chunks = await embed_memory_content(memory.content)
            await save_embedded_chunks(self._session, memory.id, chunks)
        except AIProviderError:
            pass
