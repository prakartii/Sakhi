"""Business Profile module endpoints: registration/identity CRUD plus the
onboarding/growth-workflow fields (owner, description, stage, socials) and
an onboarding-completion check.

user_id is derived from the caller's verified Supabase session
(get_current_app_user) rather than trusted from the request — create/list
silently bind to the authenticated user regardless of what a client sends.
"""

import uuid
from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.analytics.models import InventoryUsage, MetricsRows
from app.ai.analytics.summarizer import summarize
from app.ai.explanations import ExplanationRequest, explain
from app.ai.forecasting.run_rate import forecast_run_rate
from app.ai.forecasting.schemas import RunRatePoint
from app.ai.providers import AIProviderError
from app.api.deps import get_current_app_user, get_db_session
from app.models.enums import BusinessStatus, MemoryType, TransactionType
from app.models.user import User
from app.repositories.business_memory import BusinessMemoryRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.analytics_summary import (
    AISummaryResponse,
    GrowthForecastResponse,
    MemorySignalOut,
    NoticedSummaryResponse,
    RunRatePointOut,
    StockSignalOut,
    TopActionOut,
)
from app.schemas.business_profile import (
    BusinessProfileCreate,
    BusinessProfileListResponse,
    BusinessProfileOnboardingStatus,
    BusinessProfilePut,
    BusinessProfileRead,
    BusinessProfileUpdate,
)
from app.services.ai_mapping import to_ai_business_profile
from app.services.business_profile import (
    BusinessProfileConflictError,
    BusinessProfileNotFoundError,
    BusinessProfileService,
    InvalidReferenceError,
)
from app.services.inventory import InventoryService

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db_session)) -> BusinessProfileService:
    return BusinessProfileService(db)


@router.post(
    "",
    response_model=BusinessProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a business profile",
    responses={
        409: {"description": "User already has a primary business profile"},
        422: {
            "description": "Validation failed, or user_id/preferred_language_id does not exist"
        },
    },
)
async def create_business_profile(
    payload: BusinessProfileCreate,
    current_user: User = Depends(get_current_app_user),
    service: BusinessProfileService = Depends(get_service),
) -> BusinessProfileRead:
    """Create a business profile for the authenticated user.

    `is_primary` defaults to true; a user may have at most one primary
    business profile (enforced by the database) — creating a second
    primary profile returns 409. Onboarding fields (owner_name,
    business_description, target_audience, products_or_services,
    business_stage, and the social/website links) are all optional at
    creation time; use PATCH or PUT to fill them in later, and
    GET .../onboarding-status to check what's still missing.
    """
    payload.user_id = current_user.id
    try:
        return await service.create(payload)
    except BusinessProfileConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "",
    response_model=BusinessProfileListResponse,
    summary="List a user's business profiles",
)
async def list_business_profiles(
    status_filter: BusinessStatus | None = Query(
        None, alias="status", description="Filter by lifecycle status."
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_app_user),
    service: BusinessProfileService = Depends(get_service),
) -> BusinessProfileListResponse:
    """List business profiles owned by the authenticated user, newest first."""
    items, total = await service.list(
        current_user.id, status=status_filter, limit=limit, offset=offset
    )
    return BusinessProfileListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/{business_profile_id}",
    response_model=BusinessProfileRead,
    summary="Get a business profile by id",
    responses={404: {"description": "Business profile not found"}},
)
async def get_business_profile(
    business_profile_id: uuid.UUID,
    service: BusinessProfileService = Depends(get_service),
) -> BusinessProfileRead:
    try:
        return await service.get(business_profile_id)
    except BusinessProfileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Business profile not found."
        ) from exc


@router.get(
    "/{business_profile_id}/onboarding-status",
    response_model=BusinessProfileOnboardingStatus,
    summary="Get onboarding completion status",
    responses={404: {"description": "Business profile not found"}},
)
async def get_business_profile_onboarding_status(
    business_profile_id: uuid.UUID,
    service: BusinessProfileService = Depends(get_service),
) -> BusinessProfileOnboardingStatus:
    """Reports whether the profile has everything the onboarding flow
    asks for — business_name, owner_name, business_category,
    business_description, target_audience, products_or_services,
    business_stage, city, state, and country — plus which of those, if
    any, are still missing. logo_url and the social links are not counted:
    they're useful but optional, not onboarding-blocking."""
    try:
        return await service.get_onboarding_status(business_profile_id)
    except BusinessProfileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Business profile not found."
        ) from exc


@router.get(
    "/{business_profile_id}/ai-summary",
    response_model=AISummaryResponse,
    summary="AI-narrated summary of recent revenue and stock-risk facts",
    responses={
        404: {"description": "Business profile not found"},
        503: {"description": "AI provider unavailable"},
    },
)
async def get_business_profile_ai_summary(
    business_profile_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    service: BusinessProfileService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
) -> AISummaryResponse:
    """Aggregates real transactions/inventory for this business (no
    fabricated numbers — see app.ai.analytics.facts, which falls back to
    an honest "not enough data yet" fact when history is sparse) and asks
    the configured AI provider to narrate it, the same way
    app.ai.analytics.summarizer is designed to be used everywhere else."""
    try:
        profile = await service.get(business_profile_id)
    except BusinessProfileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Business profile not found."
        ) from exc
    if profile.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business profile not found.")

    transactions_repo = TransactionRepository(db)
    income, _ = await transactions_repo.list_by_business_profile(
        business_profile_id, transaction_type=TransactionType.INCOME, limit=200
    )
    weekly_totals: dict[date, float] = defaultdict(float)
    for txn in income:
        week_start = txn.transaction_date - timedelta(days=txn.transaction_date.weekday())
        weekly_totals[week_start] += float(txn.amount)
    revenue_by_period = [
        RunRatePoint(period_start=week, value=total)
        for week, total in sorted(weekly_totals.items())
    ]

    inventory_repo = InventoryRepository(db)
    low_stock, _ = await inventory_repo.list_low_stock(business_profile_id, limit=5)
    inventory_usage = [
        InventoryUsage(item_name=item.item_name, current_quantity=float(item.current_quantity))
        for item in low_stock
    ]

    metrics = MetricsRows(revenue_by_period=revenue_by_period, inventory_usage=inventory_usage)
    try:
        summary = await summarize(to_ai_business_profile(profile), metrics)
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return AISummaryResponse(
        narrative=summary.narrative,
        highlights=summary.highlights,
        top_actions=[TopActionOut(action=a.action, why=a.why) for a in summary.top_actions],
    )


@router.get(
    "/{business_profile_id}/growth-forecast",
    response_model=GrowthForecastResponse,
    summary="Weekly revenue trend, linear-regression projection, and a narrated read on it",
    responses={404: {"description": "Business profile not found"}},
)
async def get_business_profile_growth_forecast(
    business_profile_id: uuid.UUID,
    periods_ahead: int = Query(4, ge=1, le=12, description="How many future weeks to project."),
    current_user: User = Depends(get_current_app_user),
    service: BusinessProfileService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
) -> GrowthForecastResponse:
    """Projects future weekly revenue via app.ai.forecasting.run_rate's
    linear regression over logged income — deterministic, no LLM for the
    numbers. `has_sufficient_data=False` (with empty `projected`) means
    fewer than 2 distinct weeks of income are logged yet, too little to
    fit a trend. why/basis (best-effort; omitted, not failed, if the AI
    provider errors) narrate the already-computed trend and confidence,
    never invent a number."""
    try:
        profile = await service.get(business_profile_id)
    except BusinessProfileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Business profile not found."
        ) from exc
    if profile.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business profile not found.")

    transactions_repo = TransactionRepository(db)
    income, _ = await transactions_repo.list_by_business_profile(
        business_profile_id, transaction_type=TransactionType.INCOME, limit=200
    )
    weekly_totals: dict[date, float] = defaultdict(float)
    for txn in income:
        week_start = txn.transaction_date - timedelta(days=txn.transaction_date.weekday())
        weekly_totals[week_start] += float(txn.amount)
    historical = [
        RunRatePoint(period_start=week, value=total)
        for week, total in sorted(weekly_totals.items())
    ]
    historical_out = [RunRatePointOut(period_start=p.period_start, value=p.value) for p in historical]

    if len(historical) < 2:
        return GrowthForecastResponse(has_sufficient_data=False, historical=historical_out, projected=[])

    forecast = forecast_run_rate(historical, periods_ahead=periods_ahead)
    projected_out = [
        RunRatePointOut(period_start=p.period_start, value=p.value) for p in forecast.projected_periods
    ]

    direction = "growing" if forecast.trend_per_period > 0 else "shrinking" if forecast.trend_per_period < 0 else "flat"
    facts = [
        f"Weekly revenue trend is {direction}, changing by roughly Rs {abs(forecast.trend_per_period):,.0f} per week.",
        f"Recent {min(len(historical), 3)}-week moving average revenue: Rs {forecast.moving_average:,.0f}.",
        f"Projected revenue {periods_ahead} week(s) from now: Rs {forecast.projected_next_value:,.0f}.",
        f"Trend confidence (fit quality): {forecast.confidence_score:.0f} out of 100.",
    ]
    why, basis = None, None
    try:
        explanation = await explain(
            ExplanationRequest(subject="Your revenue trend and growth projection", facts=facts)
        )
        why, basis = explanation.why, explanation.basis
    except AIProviderError:
        pass

    return GrowthForecastResponse(
        has_sufficient_data=True,
        historical=historical_out,
        projected=projected_out,
        moving_average=forecast.moving_average,
        trend_per_period=forecast.trend_per_period,
        confidence_score=forecast.confidence_score,
        why=why,
        basis=basis,
    )


_STOCKOUT_ALERT_WINDOW_DAYS = 14
_NOTICED_MEMORY_LIMIT = 2


@router.get(
    "/{business_profile_id}/noticed-summary",
    response_model=NoticedSummaryResponse,
    summary="Proactive cross-module signals: stock, revenue trend, and memory, connected in one narrative",
    responses={404: {"description": "Business profile not found"}},
)
async def get_business_profile_noticed_summary(
    business_profile_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    service: BusinessProfileService = Depends(get_service),
    db: AsyncSession = Depends(get_db_session),
) -> NoticedSummaryResponse:
    """Deliberately does not repeat GET /schemes/matches — this is the one
    place in the app that looks *across* inventory, revenue and memory at
    once. Each signal is computed the same deterministic way its own page
    computes it (app.ai.forecasting.stockout / run_rate, real memory rows);
    connected_why/connected_basis only fire when at least two different
    modules actually have something to say this week, and narrate how they
    relate — the synthesis, not a re-listing of each page's own top item."""
    try:
        profile = await service.get(business_profile_id)
    except BusinessProfileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Business profile not found."
        ) from exc
    if profile.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business profile not found.")

    facts: list[str] = []

    # -- stock: only items genuinely close to running out -----------------
    inventory_repo = InventoryRepository(db)
    inventory_service = InventoryService(db, inventory_repo)
    low_stock, _ = await inventory_repo.list_low_stock(business_profile_id, limit=5)
    stock_signals: list[StockSignalOut] = []
    for item in low_stock:
        item_forecast = await inventory_service.get_forecast(item.id)
        if (
            item_forecast.has_sufficient_data
            and item_forecast.days_of_stock_remaining is not None
            and item_forecast.days_of_stock_remaining <= _STOCKOUT_ALERT_WINDOW_DAYS
        ):
            days = round(item_forecast.days_of_stock_remaining)
            stock_signals.append(
                StockSignalOut(
                    inventory_id=item.id,
                    item_name=item.item_name,
                    days_remaining=days,
                    current_quantity=float(item.current_quantity),
                    unit=item.unit,
                )
            )
            facts.append(f"{item.item_name} will run out in about {days} days.")

    # -- revenue: only a decline counts as a signal worth surfacing here ---
    transactions_repo = TransactionRepository(db)
    income, _ = await transactions_repo.list_by_business_profile(
        business_profile_id, transaction_type=TransactionType.INCOME, limit=200
    )
    weekly_totals: dict[date, float] = defaultdict(float)
    for txn in income:
        week_start = txn.transaction_date - timedelta(days=txn.transaction_date.weekday())
        weekly_totals[week_start] += float(txn.amount)
    historical = [
        RunRatePoint(period_start=week, value=total)
        for week, total in sorted(weekly_totals.items())
    ]
    revenue_trend: float | None = None
    revenue_declining = False
    if len(historical) >= 2:
        run_rate = forecast_run_rate(historical, periods_ahead=1)
        revenue_trend = run_rate.trend_per_period
        revenue_declining = run_rate.trend_per_period < 0
        if revenue_declining:
            facts.append(
                f"Weekly revenue is declining by roughly Rs {abs(run_rate.trend_per_period):,.0f} per week."
            )

    # -- memory: only unresolved challenges, not goals (those belong on
    # the Memory page, not an urgency feed) --------------------------------
    memory_repo = BusinessMemoryRepository(db)
    memories, _ = await memory_repo.list_by_business_profile(
        business_profile_id, is_archived=False, limit=50
    )
    challenges = sorted(
        (m for m in memories if m.memory_type == MemoryType.CHALLENGE),
        key=lambda m: m.importance_score,
        reverse=True,
    )[:_NOTICED_MEMORY_LIMIT]
    memory_signals = [
        MemorySignalOut(business_memory_id=m.id, title=m.title, content=m.content)
        for m in challenges
    ]
    for m in challenges:
        facts.append(f"Logged challenge: {m.title or m.content[:120]}.")

    # -- the actual USP: only narrate a connection when >=2 modules have
    # something to say — a single-domain signal is just that page's job ---
    connected_why, connected_basis = None, None
    domains_with_signals = sum(
        [bool(stock_signals), revenue_declining, bool(memory_signals)]
    )
    if domains_with_signals >= 2:
        try:
            explanation = await explain(
                ExplanationRequest(
                    subject="What's compounding across your business this week",
                    facts=facts,
                )
            )
            connected_why, connected_basis = explanation.why, explanation.basis
        except AIProviderError:
            pass

    return NoticedSummaryResponse(
        stock_signals=stock_signals,
        revenue_trend_per_week=revenue_trend,
        revenue_declining=revenue_declining,
        memory_signals=memory_signals,
        connected_why=connected_why,
        connected_basis=connected_basis,
    )


@router.patch(
    "/{business_profile_id}",
    response_model=BusinessProfileRead,
    summary="Partially update a business profile",
    responses={
        404: {"description": "Business profile not found"},
        409: {"description": "User already has a primary business profile"},
        422: {
            "description": "Validation failed, or preferred_language_id does not exist"
        },
    },
)
async def update_business_profile(
    business_profile_id: uuid.UUID,
    payload: BusinessProfileUpdate,
    service: BusinessProfileService = Depends(get_service),
) -> BusinessProfileRead:
    """Update only the fields present in the request body; omitted fields
    are left unchanged. Prefer this over PUT for incremental onboarding
    steps (e.g. setting just business_stage)."""
    try:
        return await service.update(business_profile_id, payload)
    except BusinessProfileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Business profile not found."
        ) from exc
    except BusinessProfileConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.put(
    "/{business_profile_id}",
    response_model=BusinessProfileRead,
    summary="Replace a business profile",
    responses={
        404: {"description": "Business profile not found"},
        409: {"description": "User already has a primary business profile"},
        422: {
            "description": "Validation failed, or preferred_language_id does not exist"
        },
    },
)
async def replace_business_profile(
    business_profile_id: uuid.UUID,
    payload: BusinessProfilePut,
    service: BusinessProfileService = Depends(get_service),
) -> BusinessProfileRead:
    """Replace the full profile representation. Unlike PATCH, any field
    omitted from the request body is reset to its default (empty/None for
    optional fields) rather than left as-is — send the complete profile,
    not just the fields you're changing."""
    try:
        return await service.replace(business_profile_id, payload)
    except BusinessProfileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Business profile not found."
        ) from exc
    except BusinessProfileConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.delete(
    "/{business_profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive (soft-delete) a business profile",
    responses={404: {"description": "Business profile not found"}},
)
async def delete_business_profile(
    business_profile_id: uuid.UUID,
    service: BusinessProfileService = Depends(get_service),
) -> None:
    """Sets status to 'archived' rather than deleting the row — see
    BusinessProfileService.delete for why a hard delete would be
    destructive here."""
    try:
        await service.delete(business_profile_id)
    except BusinessProfileNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Business profile not found."
        ) from exc
