"""Marketing Studio endpoints: analyze a piece of already-posted content
(caption, hashtags, metrics, comments, optional thumbnail image), or
generate a shootable brief for a new one. See
app.services.marketing_content_analysis for the orchestration and
app.ai.marketing for the AI itself.

This module is deliberately scoped to analysis and future-content
planning only — not campaign scheduling (that's Content Calendar) and not
publishing to a platform. See social_media_connections.py's docstring for
why: this app has no real Instagram Graph API credentials configured, and
obtaining them requires Meta's own App Review process, which only the
business owner can complete. `POST /marketing-studio/analyze` accepts a
`source_url` purely as a caller-supplied reference field — it is never
fetched.
"""

import base64
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.marketing import ContentMetrics, engagement_rate
from app.ai.providers.base import AIProviderError
from app.api.deps import get_current_app_user, get_db_session
from app.models.enums import MarketingAnalysisSourceType
from app.models.user import User
from app.schemas.marketing_studio import (
    GenerateReelBriefRequest,
    MarketingAnalysisListResponse,
    MarketingAnalysisOut,
)
from app.services.marketing_content_analysis import (
    BusinessProfileOrBrandNotFoundError,
    MarketingAnalysisNotFoundError,
    MarketingContentAnalysisService,
    ReelBriefRequiredError,
)

router = APIRouter()

_MAX_THUMBNAIL_BYTES = 8 * 1024 * 1024  # 8 MB — a phone-screenshot-sized image, generously


def get_service(db: AsyncSession = Depends(get_db_session)) -> MarketingContentAnalysisService:
    return MarketingContentAnalysisService(db)


def _split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def _split_csv(value: str) -> list[str]:
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def _to_out(row) -> MarketingAnalysisOut:  # noqa: ANN001 - ORM row, typed via response_model
    return MarketingAnalysisOut(
        id=row.id,
        business_profile_id=row.business_profile_id,
        social_connection_id=row.social_connection_id,
        source_type=row.source_type,
        source_url=row.source_url,
        caption=row.caption,
        hashtags=row.hashtags,
        comments_sample=row.comments_sample,
        metrics=ContentMetrics.model_validate(row.metrics),
        engagement_rate=engagement_rate(ContentMetrics.model_validate(row.metrics)),
        analysis=row.analysis,
        reel_brief=row.reel_brief,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post(
    "/analyze",
    response_model=MarketingAnalysisOut,
    status_code=status.HTTP_201_CREATED,
    summary="Analyze a piece of already-posted content — why it performed the way it did",
    responses={
        404: {"description": "Business profile not found, or has no brand kit yet"},
        413: {"description": "Thumbnail image too large"},
        503: {"description": "AI provider unavailable"},
    },
)
async def analyze_content_endpoint(
    business_profile_id: uuid.UUID = Form(...),
    social_connection_id: uuid.UUID | None = Form(None),
    source_type: MarketingAnalysisSourceType = Form(MarketingAnalysisSourceType.MANUAL),
    source_url: str | None = Form(None),
    caption: str | None = Form(None),
    hashtags: str = Form("", description="Comma-separated."),
    comments_sample: str = Form("", description="One comment per line."),
    views: int | None = Form(None),
    likes: int | None = Form(None),
    comments: int | None = Form(None),
    shares: int | None = Form(None),
    saves: int | None = Form(None),
    thumbnail: UploadFile | None = File(None, description="Optional thumbnail/screenshot image."),
    current_user: User = Depends(get_current_app_user),
    service: MarketingContentAnalysisService = Depends(get_service),
) -> MarketingAnalysisOut:
    thumbnail_data_url: str | None = None
    if thumbnail is not None:
        image_bytes = await thumbnail.read()
        if len(image_bytes) > _MAX_THUMBNAIL_BYTES:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Thumbnail image too large.")
        if image_bytes:
            content_type = thumbnail.content_type or "image/jpeg"
            encoded = base64.b64encode(image_bytes).decode("ascii")
            thumbnail_data_url = f"data:{content_type};base64,{encoded}"

    try:
        row = await service.analyze(
            user_id=current_user.id,
            business_profile_id=business_profile_id,
            social_connection_id=social_connection_id,
            source_type=source_type,
            source_url=source_url,
            caption=caption,
            hashtags=_split_csv(hashtags),
            comments_sample=_split_lines(comments_sample),
            metrics=ContentMetrics(views=views, likes=likes, comments=comments, shares=shares, saves=saves),
            thumbnail_data_url=thumbnail_data_url,
        )
    except BusinessProfileOrBrandNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return _to_out(row)


@router.post(
    "/generate-reel",
    response_model=MarketingAnalysisOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a shootable brief for a new reel — script, shot list, caption, hashtags",
    responses={
        404: {"description": "Business profile not found, or has no brand kit yet"},
        503: {"description": "AI provider unavailable"},
    },
)
async def generate_reel_endpoint(
    payload: GenerateReelBriefRequest,
    current_user: User = Depends(get_current_app_user),
    service: MarketingContentAnalysisService = Depends(get_service),
) -> MarketingAnalysisOut:
    """Produces a brief (hook, script beats, shot list, caption, hashtags,
    CTA) grounded in this business's products and brand voice, informed by
    what's already worked (or not) in its own past analyses — not a
    rendered video. This app has no video-generation capability."""
    try:
        row = await service.generate_reel(
            user_id=current_user.id,
            business_profile_id=payload.business_profile_id,
            angle=payload.angle,
        )
    except BusinessProfileOrBrandNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return _to_out(row)


@router.post(
    "/{analysis_id}/generate-visual",
    response_model=MarketingAnalysisOut,
    summary="Generate a cover visual for a reel brief with Nano Banana (Gemini 2.5 Flash Image) — free tier",
    responses={
        404: {"description": "Analysis not found, or not owned by the caller"},
        422: {"description": "This analysis has no reel brief yet — generate one first"},
        503: {"description": "Image provider unavailable"},
    },
)
async def generate_visual_endpoint(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    service: MarketingContentAnalysisService = Depends(get_service),
) -> MarketingAnalysisOut:
    """Additive, not part of /generate-reel — a caller opts into this per
    brief. Free tier (same GEMINI_API_KEY as embeddings), unlike
    generate-video below."""
    try:
        row = await service.generate_visual(analysis_id=analysis_id, user_id=current_user.id)
    except (MarketingAnalysisNotFoundError, BusinessProfileOrBrandNotFoundError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc) or "Analysis not found.") from exc
    except ReelBriefRequiredError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return _to_out(row)


@router.post(
    "/{analysis_id}/generate-video",
    response_model=MarketingAnalysisOut,
    summary="Generate a video for a reel brief with fal.ai — real, billed API call, no free tier",
    responses={
        404: {"description": "Analysis not found, or not owned by the caller"},
        422: {"description": "This analysis has no reel brief yet — generate one first"},
        503: {"description": "Video provider unavailable"},
    },
)
async def generate_video_endpoint(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    service: MarketingContentAnalysisService = Depends(get_service),
) -> MarketingAnalysisOut:
    """Additive, not part of /generate-reel — a caller opts into this per
    brief, deliberately: fal.ai has no ongoing free tier (a one-time
    signup credit, then pay-per-second), so this must never fire
    automatically."""
    try:
        row = await service.generate_video(analysis_id=analysis_id, user_id=current_user.id)
    except (MarketingAnalysisNotFoundError, BusinessProfileOrBrandNotFoundError) as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc) or "Analysis not found.") from exc
    except ReelBriefRequiredError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return _to_out(row)


@router.get(
    "",
    response_model=MarketingAnalysisListResponse,
    summary="List a business's Marketing Studio history — analyses and generated reel briefs",
)
async def list_analyses(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: MarketingContentAnalysisService = Depends(get_service),
) -> MarketingAnalysisListResponse:
    items, total = await service.list(business_profile_id, limit=limit, offset=offset)
    return MarketingAnalysisListResponse(
        items=[_to_out(item) for item in items], total=total, limit=limit, offset=offset
    )


@router.get(
    "/{analysis_id}",
    response_model=MarketingAnalysisOut,
    summary="Get one Marketing Studio analysis or generated reel brief by id",
    responses={404: {"description": "Not found"}},
)
async def get_analysis(
    analysis_id: uuid.UUID,
    service: MarketingContentAnalysisService = Depends(get_service),
) -> MarketingAnalysisOut:
    try:
        row = await service.get(analysis_id)
    except MarketingAnalysisNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Analysis not found.") from exc
    return _to_out(row)
