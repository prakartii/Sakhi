"""Marketing Analytics endpoints.

Storage + simple aggregation only: Store Snapshot persists a reading a
caller already has; every other endpoint here is a sum/avg/count over
stored rows, computed in Postgres. Nothing here calls a platform API and
nothing here forecasts.

No authentication yet: business_profile_id is supplied explicitly by the
caller (request body on store, required query param everywhere else)
instead of being derived from a session — the same deliberate, temporary
gap already documented on every other module's endpoints.

Route order below matters: "/daily", "/weekly", "/monthly", "/compare",
and "/summary" are literal single-segment GET paths and must be registered
before the parametrized "/{snapshot_id}" GET at the same depth, or FastAPI
would try to parse them as a UUID path param — the same hazard class
already documented on the Inventory/Content Calendar/Scheduled Posts
routers.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.schemas.marketing_analytics_snapshot import (
    AnalyticsSummary,
    MarketingAnalyticsSnapshotCreate,
    MarketingAnalyticsSnapshotRead,
    PeriodAnalyticsListResponse,
    PeriodComparison,
)
from app.services.marketing_analytics_snapshot import (
    InvalidReferenceError,
    InvalidSnapshotError,
    InvalidSocialConnectionError,
    MarketingAnalyticsSnapshotNotFoundError,
    MarketingAnalyticsSnapshotService,
)

router = APIRouter()


def get_service(
    db: AsyncSession = Depends(get_db_session),
) -> MarketingAnalyticsSnapshotService:
    return MarketingAnalyticsSnapshotService(db)


@router.post(
    "",
    response_model=MarketingAnalyticsSnapshotRead,
    status_code=status.HTTP_201_CREATED,
    summary="Store an analytics snapshot",
    responses={
        422: {
            "description": "Validation failed, captured_at is in the future, "
            "business_profile_id does not exist, or social_connection_id is "
            "invalid for this business"
        },
    },
)
async def store_snapshot(
    payload: MarketingAnalyticsSnapshotCreate,
    service: MarketingAnalyticsSnapshotService = Depends(get_service),
) -> MarketingAnalyticsSnapshotRead:
    """Record a point-in-time analytics reading. Every metric is optional
    — store whatever was actually available at capture time."""
    try:
        return await service.store_snapshot(payload)
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except InvalidSocialConnectionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except InvalidSnapshotError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "/daily",
    response_model=PeriodAnalyticsListResponse,
    summary="Get daily analytics",
)
async def get_daily_analytics(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    start: datetime = Query(..., description="Range start (inclusive)."),
    end: datetime = Query(..., description="Range end (exclusive)."),
    social_connection_id: uuid.UUID | None = Query(
        None, description="Narrow to one connected account."
    ),
    service: MarketingAnalyticsSnapshotService = Depends(get_service),
) -> PeriodAnalyticsListResponse:
    """One aggregate bucket per day that has at least one snapshot in
    [start, end)."""
    items = await service.get_daily_analytics(
        business_profile_id,
        start=start,
        end=end,
        social_connection_id=social_connection_id,
    )
    return PeriodAnalyticsListResponse(items=items)


@router.get(
    "/weekly",
    response_model=PeriodAnalyticsListResponse,
    summary="Get weekly analytics",
)
async def get_weekly_analytics(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    start: datetime = Query(..., description="Range start (inclusive)."),
    end: datetime = Query(..., description="Range end (exclusive)."),
    social_connection_id: uuid.UUID | None = Query(
        None, description="Narrow to one connected account."
    ),
    service: MarketingAnalyticsSnapshotService = Depends(get_service),
) -> PeriodAnalyticsListResponse:
    """One aggregate bucket per week that has at least one snapshot in
    [start, end)."""
    items = await service.get_weekly_analytics(
        business_profile_id,
        start=start,
        end=end,
        social_connection_id=social_connection_id,
    )
    return PeriodAnalyticsListResponse(items=items)


@router.get(
    "/monthly",
    response_model=PeriodAnalyticsListResponse,
    summary="Get monthly analytics",
)
async def get_monthly_analytics(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    start: datetime = Query(..., description="Range start (inclusive)."),
    end: datetime = Query(..., description="Range end (exclusive)."),
    social_connection_id: uuid.UUID | None = Query(
        None, description="Narrow to one connected account."
    ),
    service: MarketingAnalyticsSnapshotService = Depends(get_service),
) -> PeriodAnalyticsListResponse:
    """One aggregate bucket per calendar month that has at least one
    snapshot in [start, end)."""
    items = await service.get_monthly_analytics(
        business_profile_id,
        start=start,
        end=end,
        social_connection_id=social_connection_id,
    )
    return PeriodAnalyticsListResponse(items=items)


@router.get(
    "/compare",
    response_model=PeriodComparison,
    summary="Compare two time periods",
)
async def compare_periods(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    period_a_start: datetime = Query(
        ..., description="First period start (inclusive)."
    ),
    period_a_end: datetime = Query(..., description="First period end (exclusive)."),
    period_b_start: datetime = Query(
        ..., description="Second period start (inclusive)."
    ),
    period_b_end: datetime = Query(..., description="Second period end (exclusive)."),
    social_connection_id: uuid.UUID | None = Query(
        None, description="Narrow to one connected account."
    ),
    service: MarketingAnalyticsSnapshotService = Depends(get_service),
) -> PeriodComparison:
    """Aggregates both periods and returns the change (absolute and
    percent) for every metric from period_a to period_b."""
    return await service.compare_periods(
        business_profile_id,
        period_a_start=period_a_start,
        period_a_end=period_a_end,
        period_b_start=period_b_start,
        period_b_end=period_b_end,
        social_connection_id=social_connection_id,
    )


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    summary="Get an analytics summary",
)
async def summary(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    days: int = Query(
        30, ge=1, le=365, description="Rolling window size in days, ending now."
    ),
    social_connection_id: uuid.UUID | None = Query(
        None, description="Narrow to one connected account."
    ),
    service: MarketingAnalyticsSnapshotService = Depends(get_service),
) -> AnalyticsSummary:
    """Rolling-window aggregate (default last 30 days) plus the most
    recently captured snapshot."""
    return await service.summary(
        business_profile_id, days=days, social_connection_id=social_connection_id
    )


@router.get(
    "/{snapshot_id}",
    response_model=MarketingAnalyticsSnapshotRead,
    summary="Get a snapshot by id",
    responses={404: {"description": "Snapshot not found"}},
)
async def get_snapshot(
    snapshot_id: uuid.UUID,
    service: MarketingAnalyticsSnapshotService = Depends(get_service),
) -> MarketingAnalyticsSnapshotRead:
    try:
        return await service.get(snapshot_id)
    except MarketingAnalyticsSnapshotNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Snapshot not found.") from exc
