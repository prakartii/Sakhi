"""Finance (Transaction) CRUD endpoints.

No authentication yet: business_profile_id is supplied explicitly by the
caller (request body on create, required query param on list) instead of
being derived from a session — the same deliberate, temporary gap already
documented on the Business Profile, Brand Assets, and Website endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.enums import TransactionStatus, TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionRead,
    TransactionUpdate,
)
from app.services.transaction import (
    InvalidReferenceError,
    InvalidTransactionError,
    TransactionNotFoundError,
    TransactionService,
)

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db_session)) -> TransactionService:
    return TransactionService(db)


@router.post(
    "",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Record a transaction",
    responses={
        422: {
            "description": "Validation failed, business_profile_id/supplier_id does "
            "not exist, or is_recurring is true with no recurring_frequency"
        },
    },
)
async def create_transaction(
    payload: TransactionCreate,
    service: TransactionService = Depends(get_service),
) -> TransactionRead:
    """Record an income or expense event. `status` defaults to `completed`
    and `source` to `manual`."""
    try:
        return await service.create(payload)
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except InvalidTransactionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List a business's transactions",
)
async def list_transactions(
    business_profile_id: uuid.UUID = Query(
        ...,
        description="Owning business id (temporary — replaced by session-derived "
        "scoping once auth exists).",
    ),
    transaction_type: TransactionType | None = Query(
        None, description="Filter by income/expense."
    ),
    status_filter: TransactionStatus | None = Query(
        None, alias="status", description="Filter by payment status."
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: TransactionService = Depends(get_service),
) -> TransactionListResponse:
    """List transactions owned by a given business, most recent first."""
    items, total = await service.list(
        business_profile_id,
        transaction_type=transaction_type,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return TransactionListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Get a transaction by id",
    responses={404: {"description": "Transaction not found"}},
)
async def get_transaction(
    transaction_id: uuid.UUID,
    service: TransactionService = Depends(get_service),
) -> TransactionRead:
    try:
        return await service.get(transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Transaction not found."
        ) from exc


@router.patch(
    "/{transaction_id}",
    response_model=TransactionRead,
    summary="Partially update a transaction",
    responses={
        404: {"description": "Transaction not found"},
        422: {
            "description": "Validation failed, supplier_id does not exist, or the "
            "resulting is_recurring/recurring_frequency combination is invalid"
        },
    },
)
async def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    service: TransactionService = Depends(get_service),
) -> TransactionRead:
    """Update only the fields present in the request body; omitted fields
    are left unchanged."""
    try:
        return await service.update(transaction_id, payload)
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Transaction not found."
        ) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except InvalidTransactionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction",
    responses={404: {"description": "Transaction not found"}},
)
async def delete_transaction(
    transaction_id: uuid.UUID,
    service: TransactionService = Depends(get_service),
) -> None:
    """Permanently deletes the record — see TransactionService.delete for
    why this module has no soft-delete, unlike Business Profile/Brand
    Assets/Website."""
    try:
        await service.delete(transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Transaction not found."
        ) from exc
