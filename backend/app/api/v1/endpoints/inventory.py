"""Inventory (Smart Inventory) endpoints: product CRUD, stock operations,
movement history, low-stock/out-of-stock views, and a summary.

Route order matters here: /low-stock, /out-of-stock and /summary are
registered before /{inventory_id} on purpose. FastAPI/Starlette matches
path templates in registration order, and a single literal segment
("low-stock") and a single path-parameter segment ("{inventory_id}") sit
at the same depth — if the parametrized route were registered first, a
request to /inventory/low-stock would incorrectly match it with
inventory_id="low-stock" and fail UUID parsing instead of reaching this
endpoint.

No authentication yet: business_profile_id is supplied explicitly by the
caller (request body on create, required query param on list) instead of
being derived from a session — the same deliberate, temporary gap already
documented on every other endpoint module in this project.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.enums import InventoryMovementType
from app.schemas.inventory import (
    InventoryCreate,
    InventoryForecastResponse,
    InventoryListResponse,
    InventoryMovementListResponse,
    InventoryRead,
    InventorySummary,
    InventoryUpdate,
    StockAdjustmentRequest,
    StockInRequest,
    StockOutRequest,
)
from app.services.inventory import (
    InsufficientStockError,
    InventoryConflictError,
    InventoryNotFoundError,
    InventoryService,
    InvalidReferenceError,
)

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db_session)) -> InventoryService:
    return InventoryService(db)


@router.post(
    "",
    response_model=InventoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
    responses={
        409: {
            "description": "sku is already in use by another product for this business"
        },
        422: {
            "description": "Validation failed, or business_profile_id/supplier_id does not exist"
        },
    },
)
async def create_product(
    payload: InventoryCreate,
    service: InventoryService = Depends(get_service),
) -> InventoryRead:
    """Create a product. If `current_quantity` is greater than 0, an
    initial stock movement is recorded automatically."""
    try:
        return await service.create(payload)
    except InventoryConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "/low-stock",
    response_model=InventoryListResponse,
    summary="Get low-stock products",
)
async def list_low_stock_products(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: InventoryService = Depends(get_service),
) -> InventoryListResponse:
    """Active products with stock at or below their reorder level but not
    yet at zero, most urgent (lowest stock) first."""
    items, total = await service.list_low_stock(
        business_profile_id, limit=limit, offset=offset
    )
    return InventoryListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/out-of-stock",
    response_model=InventoryListResponse,
    summary="Get out-of-stock products",
)
async def list_out_of_stock_products(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: InventoryService = Depends(get_service),
) -> InventoryListResponse:
    """Active products with zero stock on hand."""
    items, total = await service.list_out_of_stock(
        business_profile_id, limit=limit, offset=offset
    )
    return InventoryListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/summary",
    response_model=InventorySummary,
    summary="Get inventory summary",
)
async def get_inventory_summary(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    service: InventoryService = Depends(get_service),
) -> InventorySummary:
    """Total active products, total stock value at cost, and low-stock/
    out-of-stock counts for one business."""
    return InventorySummary(**await service.get_summary(business_profile_id))


@router.get(
    "",
    response_model=InventoryListResponse,
    summary="List or search a business's products",
)
async def list_products(
    business_profile_id: uuid.UUID = Query(
        ...,
        description="Owning business id (temporary — replaced by session-derived "
        "scoping once auth exists).",
    ),
    q: str | None = Query(
        None, description="Substring search over item_name/sku/category."
    ),
    category: str | None = Query(None, description="Filter by exact category."),
    supplier_id: uuid.UUID | None = Query(None, description="Filter by supplier."),
    is_active: bool | None = Query(None, description="Filter by active status."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: InventoryService = Depends(get_service),
) -> InventoryListResponse:
    """Lists a business's products; pass `q` to search by name/SKU/
    category instead. Every filter (category/supplier_id/is_active)
    applies whether or not `q` is given."""
    items, total = await service.list(
        business_profile_id,
        q=q,
        category=category,
        supplier_id=supplier_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return InventoryListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{inventory_id}",
    response_model=InventoryRead,
    summary="Get a product by id",
    responses={404: {"description": "Product not found"}},
)
async def get_product(
    inventory_id: uuid.UUID,
    service: InventoryService = Depends(get_service),
) -> InventoryRead:
    try:
        return await service.get(inventory_id)
    except InventoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.") from exc


@router.get(
    "/{inventory_id}/movements",
    response_model=InventoryMovementListResponse,
    summary="Get a product's inventory movement history",
    responses={404: {"description": "Product not found"}},
)
async def list_product_movements(
    inventory_id: uuid.UUID,
    movement_type: InventoryMovementType | None = Query(
        None, description="Filter by movement type."
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: InventoryService = Depends(get_service),
) -> InventoryMovementListResponse:
    """Newest-first ledger of every stock change for this product —
    creation's initial stock, stock_in, stock_out, and adjustments."""
    try:
        items, total = await service.list_movements(
            inventory_id, movement_type=movement_type, limit=limit, offset=offset
        )
    except InventoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.") from exc
    return InventoryMovementListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/{inventory_id}/forecast",
    response_model=InventoryForecastResponse,
    summary="AI-projected stockout date for a product (app.ai.forecasting, deterministic run-rate)",
    responses={404: {"description": "Product not found"}},
)
async def get_product_forecast(
    inventory_id: uuid.UUID,
    window_days: int = Query(30, ge=7, le=90, description="Lookback window for the consumption rate."),
    lead_time_days: int | None = Query(
        None, ge=0, le=180, description="Supplier lead time, for a reorder-by date."
    ),
    service: InventoryService = Depends(get_service),
) -> InventoryForecastResponse:
    """Projects when this product runs out from its own sale/wastage
    history — no LLM, see app.ai.forecasting.stockout.forecast_stockout.
    `has_sufficient_data=False` (with no projected dates) means there's
    too little history yet, not that the product is safe."""
    try:
        forecast = await service.get_forecast(
            inventory_id, window_days=window_days, lead_time_days=lead_time_days
        )
    except InventoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.") from exc
    return InventoryForecastResponse(**forecast.model_dump())


@router.patch(
    "/{inventory_id}",
    response_model=InventoryRead,
    summary="Partially update a product",
    responses={
        404: {"description": "Product not found"},
        409: {
            "description": "sku is already in use by another product for this business"
        },
        422: {"description": "Validation failed, or supplier_id does not exist"},
    },
)
async def update_product(
    inventory_id: uuid.UUID,
    payload: InventoryUpdate,
    service: InventoryService = Depends(get_service),
) -> InventoryRead:
    """Update only the fields present in the request body; omitted fields
    are left unchanged. Cannot change stock on hand — use stock-in/
    stock-out/adjust instead."""
    try:
        return await service.update(inventory_id, payload)
    except InventoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.") from exc
    except InventoryConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.post(
    "/{inventory_id}/stock-in",
    response_model=InventoryRead,
    summary="Stock in (increase quantity)",
    responses={
        404: {"description": "Product not found"},
        422: {
            "description": "Validation failed, or related_transaction_id does not exist"
        },
    },
)
async def stock_in(
    inventory_id: uuid.UUID,
    payload: StockInRequest,
    service: InventoryService = Depends(get_service),
) -> InventoryRead:
    """Adds `quantity` to stock on hand and records a `restock`
    movement."""
    try:
        return await service.stock_in(inventory_id, payload)
    except InventoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.") from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.post(
    "/{inventory_id}/stock-out",
    response_model=InventoryRead,
    summary="Stock out (decrease quantity)",
    responses={
        404: {"description": "Product not found"},
        409: {"description": "Requested quantity exceeds current stock"},
        422: {
            "description": "Validation failed, or related_transaction_id does not exist"
        },
    },
)
async def stock_out(
    inventory_id: uuid.UUID,
    payload: StockOutRequest,
    service: InventoryService = Depends(get_service),
) -> InventoryRead:
    """Removes `quantity` from stock on hand and records a `sale`
    movement. Rejected with 409 if it would take stock negative."""
    try:
        return await service.stock_out(inventory_id, payload)
    except InventoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.") from exc
    except InsufficientStockError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.post(
    "/{inventory_id}/adjust",
    response_model=InventoryRead,
    summary="Manually adjust stock to a known quantity",
    responses={
        404: {"description": "Product not found"},
        422: {"description": "Validation failed"},
    },
)
async def adjust_stock(
    inventory_id: uuid.UUID,
    payload: StockAdjustmentRequest,
    service: InventoryService = Depends(get_service),
) -> InventoryRead:
    """Sets stock on hand to `new_quantity` (e.g. after a physical count)
    and records an `adjustment` movement for the difference."""
    try:
        return await service.adjust_stock(inventory_id, payload)
    except InventoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.") from exc


@router.delete(
    "/{inventory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a product",
    responses={404: {"description": "Product not found"}},
)
async def delete_product(
    inventory_id: uuid.UUID,
    service: InventoryService = Depends(get_service),
) -> None:
    """Sets is_active to false rather than deleting the row — see
    InventoryService.delete for why."""
    try:
        await service.delete(inventory_id)
    except InventoryNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.") from exc
