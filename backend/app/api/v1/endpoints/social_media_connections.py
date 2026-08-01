"""Social Media Connections endpoints.

Stores and manages *authenticated* platform connections — distinct from the
plain instagram_url/facebook_url/linkedin_url profile links already on
Business Profile. No platform API is called by anything in this router:
"Refresh Token" and "Sync Metadata" both record data a caller already
obtained elsewhere (a future OAuth-handling module, or a manual operation),
they don't fetch it. No post-publishing lives here either.

Access tokens are never present in any response — see
app.schemas.social_media_connection's module docstring and
SocialMediaConnectionRead, which simply has no token field.

No authentication yet: business_profile_id is supplied explicitly by the
caller (request body on connect, required query param on list) instead of
being derived from a session — the same deliberate, temporary gap already
documented on every other module's endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.enums import SocialConnectionStatus, SocialMediaPlatform
from app.schemas.social_media_connection import (
    RefreshTokenRequest,
    SocialMediaConnectionCreate,
    SocialMediaConnectionListResponse,
    SocialMediaConnectionRead,
    SyncMetadataRequest,
)
from app.services.social_media_connection import (
    InvalidReferenceError,
    SocialMediaConnectionNotFoundError,
    SocialMediaConnectionService,
)

router = APIRouter()


def get_service(
    db: AsyncSession = Depends(get_db_session),
) -> SocialMediaConnectionService:
    return SocialMediaConnectionService(db)


@router.post(
    "",
    response_model=SocialMediaConnectionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Connect a social media account",
    responses={
        422: {
            "description": "Validation failed, or business_profile_id does not exist"
        },
    },
)
async def connect_account(
    payload: SocialMediaConnectionCreate,
    service: SocialMediaConnectionService = Depends(get_service),
) -> SocialMediaConnectionRead:
    """Store an authenticated connection for one platform. Reconnecting a
    platform that's already connected for this business updates the
    existing row (fresh tokens, status back to `connected`) rather than
    creating a duplicate — each business has at most one connection per
    platform."""
    try:
        return await service.connect(payload)
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "",
    response_model=SocialMediaConnectionListResponse,
    summary="List a business's connected accounts",
)
async def list_connections(
    business_profile_id: uuid.UUID = Query(
        ...,
        description="Owning business id (temporary — replaced by session-derived "
        "scoping once auth exists).",
    ),
    platform: SocialMediaPlatform | None = Query(
        None, description="Filter by platform."
    ),
    connection_status: SocialConnectionStatus | None = Query(
        None, description="Filter by connection status."
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: SocialMediaConnectionService = Depends(get_service),
) -> SocialMediaConnectionListResponse:
    """List a business's connected platform accounts. Never includes
    tokens — see SocialMediaConnectionRead."""
    items, total = await service.list(
        business_profile_id,
        platform=platform,
        connection_status=connection_status,
        limit=limit,
        offset=offset,
    )
    return SocialMediaConnectionListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/{connection_id}",
    response_model=SocialMediaConnectionRead,
    summary="Get a connected account by id",
    responses={404: {"description": "Connection not found"}},
)
async def get_connection(
    connection_id: uuid.UUID,
    service: SocialMediaConnectionService = Depends(get_service),
) -> SocialMediaConnectionRead:
    try:
        return await service.get(connection_id)
    except SocialMediaConnectionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connection not found.") from exc


@router.post(
    "/{connection_id}/disconnect",
    response_model=SocialMediaConnectionRead,
    summary="Disconnect a social media account",
    responses={404: {"description": "Connection not found"}},
)
async def disconnect_account(
    connection_id: uuid.UUID,
    service: SocialMediaConnectionService = Depends(get_service),
) -> SocialMediaConnectionRead:
    """Sets connection_status to `disconnected` and clears the stored
    tokens — see SocialMediaConnectionService.disconnect."""
    try:
        return await service.disconnect(connection_id)
    except SocialMediaConnectionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connection not found.") from exc


@router.post(
    "/{connection_id}/refresh-token",
    response_model=SocialMediaConnectionRead,
    summary="Record a refreshed token for a connection",
    responses={404: {"description": "Connection not found"}},
)
async def refresh_token(
    connection_id: uuid.UUID,
    payload: RefreshTokenRequest,
    service: SocialMediaConnectionService = Depends(get_service),
) -> SocialMediaConnectionRead:
    """Persists a token obtained elsewhere and marks the connection
    `connected` again. Does not call the platform's API — see
    SocialMediaConnectionService.refresh_token."""
    try:
        return await service.refresh_token(connection_id, payload)
    except SocialMediaConnectionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connection not found.") from exc


@router.post(
    "/{connection_id}/sync-metadata",
    response_model=SocialMediaConnectionRead,
    summary="Record refreshed account metadata for a connection",
    responses={404: {"description": "Connection not found"}},
)
async def sync_metadata(
    connection_id: uuid.UUID,
    payload: SyncMetadataRequest,
    service: SocialMediaConnectionService = Depends(get_service),
) -> SocialMediaConnectionRead:
    """Persists account metadata obtained elsewhere and stamps last_sync.
    Does not call the platform's API — see
    SocialMediaConnectionService.sync_metadata."""
    try:
        return await service.sync_metadata(connection_id, payload)
    except SocialMediaConnectionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Connection not found.") from exc
