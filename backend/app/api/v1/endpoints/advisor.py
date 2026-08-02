"""AI Advisor: a grounded, ongoing chat over a business's own data.

POST /advisor/chat routes each message through app.ai.orchestrator.handle,
which decides (via deterministic phrase-matching, no LLM — see
app.ai.orchestrator.router) which generation services a question is
relevant to, assembles facts only from what's already been generated for
this business (brand kit, revenue/inventory metrics, retrieved
business_memory), and answers grounded in those facts alone — the model
never invents a number or fact itself.

One continuous thread per business: chat history is stored in the existing
conversation_history table, keyed by session_id = business_profile_id
(distinct from Website Studio's session_id = website.id, so the two
threads never collide despite sharing a business_profile_id).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.analytics.models import InventoryUsage, MetricsRows
from app.ai.forecasting.schemas import RunRatePoint
from app.ai.orchestrator import OrchestratorContext
from app.ai.orchestrator import handle as ai_handle
from app.ai.providers.base import AIProviderError
from app.api.deps import get_current_app_user, get_db_session
from app.models.conversation_history import ConversationHistory
from app.models.enums import ConversationMessageType, ConversationRole, TransactionType
from app.models.user import User
from app.repositories.brand_asset import BrandAssetRepository
from app.repositories.business_profile import BusinessProfileRepository
from app.repositories.conversation_history import ConversationHistoryRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.advisor import (
    AdvisorChatHistoryResponse,
    AdvisorChatMessageOut,
    AdvisorChatRequest,
    AdvisorChatResponse,
)
from app.services.ai_mapping import to_ai_brand_kit, to_ai_business_profile

router = APIRouter()

_HISTORY_LIMIT = 50


async def _get_owned_profile(
    db: AsyncSession, business_profile_id: uuid.UUID, current_user: User
):
    profiles = BusinessProfileRepository(db)
    profile = await profiles.get_by_id(business_profile_id)
    if profile is None or profile.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business profile not found.")
    return profile


async def _build_metrics(db: AsyncSession, business_profile_id: uuid.UUID) -> MetricsRows:
    """Same real-transactions/real-inventory aggregation as
    GET /business-profiles/{id}/ai-summary — no fabricated numbers."""
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
    return MetricsRows(revenue_by_period=revenue_by_period, inventory_usage=inventory_usage)


@router.post(
    "/chat",
    response_model=AdvisorChatResponse,
    summary="Ask Sakhi's AI Advisor one question, grounded in this business's own data",
    responses={
        404: {"description": "Business profile not found or not owned by the caller"},
        422: {"description": "message was empty"},
        503: {"description": "AI provider unavailable"},
    },
)
async def advisor_chat(
    payload: AdvisorChatRequest,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db_session),
) -> AdvisorChatResponse:
    profile = await _get_owned_profile(db, payload.business_profile_id, current_user)

    brand_assets = BrandAssetRepository(db)
    brands, _ = await brand_assets.list_by_business_profile(profile.id, limit=1)
    brand_kit = to_ai_brand_kit(brands[0]) if brands else None
    metrics = await _build_metrics(db, profile.id)

    try:
        result = await ai_handle(
            payload.message,
            to_ai_business_profile(profile),
            OrchestratorContext(brand=brand_kit, metrics=metrics),
            session=db,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    conversation = ConversationHistoryRepository(db)
    await conversation.create(
        ConversationHistory(
            business_profile_id=profile.id,
            user_id=current_user.id,
            session_id=profile.id,
            role=ConversationRole.USER,
            message_type=ConversationMessageType.TEXT,
            content=payload.message,
        )
    )
    await conversation.create(
        ConversationHistory(
            business_profile_id=profile.id,
            user_id=current_user.id,
            session_id=profile.id,
            role=ConversationRole.ASSISTANT,
            message_type=ConversationMessageType.TEXT,
            content=result.answer,
        )
    )
    await db.commit()

    return AdvisorChatResponse(
        answer=result.answer, used_services=result.used_services, sources=result.sources
    )


@router.get(
    "/{business_profile_id}/chat",
    response_model=AdvisorChatHistoryResponse,
    summary="This business's AI Advisor conversation history, oldest first",
    responses={404: {"description": "Business profile not found or not owned by the caller"}},
)
async def advisor_chat_history(
    business_profile_id: uuid.UUID,
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db_session),
) -> AdvisorChatHistoryResponse:
    await _get_owned_profile(db, business_profile_id, current_user)
    conversation = ConversationHistoryRepository(db)
    turns, _ = await conversation.list_by_session(business_profile_id, limit=_HISTORY_LIMIT)
    return AdvisorChatHistoryResponse(
        messages=[
            AdvisorChatMessageOut(role=t.role.value, content=t.content, created_at=t.created_at)
            for t in turns
        ]
    )
