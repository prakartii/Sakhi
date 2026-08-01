"""Website Management endpoints: metadata CRUD plus read-only version
history.

Storage only: website_name, deployment_url, github_repository, template,
status, seo_title/description, custom_domain, favicon, published. No
deployment, no generation — this module reads and writes website metadata
a caller (human or, later, a separate deploy service) provides. Version
history is produced automatically as a side effect of create/update/delete
(see WebsiteService) — there is deliberately no endpoint to author a
version by hand.

No authentication yet: business_profile_id is supplied explicitly by the
caller (request body on create, required query param on list) instead of
being derived from a session — the same deliberate, temporary gap already
documented on the Business Profile and Brand Assets endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.enums import WebsiteStatus
from app.schemas.website import (
    WebsiteCreate,
    WebsiteListResponse,
    WebsiteRead,
    WebsiteUpdate,
    WebsiteVersionListResponse,
    WebsiteVersionRead,
)
from app.services.website import (
    InvalidReferenceError,
    WebsiteConflictError,
    WebsiteNotFoundError,
    WebsiteService,
    WebsiteVersionNotFoundError,
)

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db_session)) -> WebsiteService:
    return WebsiteService(db)


@router.post(
    "",
    response_model=WebsiteRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a website",
    responses={
        409: {"description": "custom_domain is already in use by another website"},
        422: {
            "description": "Validation failed, or business_profile_id does not exist"
        },
    },
)
async def create_website(
    payload: WebsiteCreate,
    service: WebsiteService = Depends(get_service),
) -> WebsiteRead:
    """Create a website metadata record for a business. `status` defaults
    to `draft`. Automatically records version 1 of the site's history."""
    try:
        return await service.create(payload)
    except WebsiteConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "",
    response_model=WebsiteListResponse,
    summary="List a business's websites",
)
async def list_websites(
    business_profile_id: uuid.UUID = Query(
        ...,
        description="Owning business id (temporary — replaced by session-derived "
        "scoping once auth exists).",
    ),
    status_filter: WebsiteStatus | None = Query(
        None, alias="status", description="Filter by lifecycle status."
    ),
    published: bool | None = Query(None, description="Filter by published flag."),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: WebsiteService = Depends(get_service),
) -> WebsiteListResponse:
    """List websites owned by a given business, newest first."""
    items, total = await service.list(
        business_profile_id,
        status=status_filter,
        published=published,
        limit=limit,
        offset=offset,
    )
    return WebsiteListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{website_id}",
    response_model=WebsiteRead,
    summary="Get a website by id",
    responses={404: {"description": "Website not found"}},
)
async def get_website(
    website_id: uuid.UUID,
    service: WebsiteService = Depends(get_service),
) -> WebsiteRead:
    try:
        return await service.get(website_id)
    except WebsiteNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Website not found.") from exc


@router.get(
    "/{website_id}/versions",
    response_model=WebsiteVersionListResponse,
    summary="List a website's version history",
    responses={404: {"description": "Website not found"}},
)
async def list_website_versions(
    website_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: WebsiteService = Depends(get_service),
) -> WebsiteVersionListResponse:
    """Newest-first snapshot history. A version is recorded automatically
    on every create/update/delete of the website — there's no way to
    create one directly."""
    try:
        items, total = await service.list_versions(
            website_id, limit=limit, offset=offset
        )
    except WebsiteNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Website not found.") from exc
    return WebsiteVersionListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/{website_id}/versions/{version_number}",
    response_model=WebsiteVersionRead,
    summary="Get a single version from a website's history",
    responses={404: {"description": "Website or version not found"}},
)
async def get_website_version(
    website_id: uuid.UUID,
    version_number: int,
    service: WebsiteService = Depends(get_service),
) -> WebsiteVersionRead:
    try:
        return await service.get_version(website_id, version_number)
    except WebsiteNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Website not found.") from exc
    except WebsiteVersionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Version not found.") from exc


@router.patch(
    "/{website_id}",
    response_model=WebsiteRead,
    summary="Partially update a website",
    responses={
        404: {"description": "Website not found"},
        409: {"description": "custom_domain is already in use by another website"},
        422: {"description": "Validation failed"},
    },
)
async def update_website(
    website_id: uuid.UUID,
    payload: WebsiteUpdate,
    service: WebsiteService = Depends(get_service),
) -> WebsiteRead:
    """Update only the fields present in the request body; omitted fields
    are left unchanged. Always records a new version snapshot of the
    resulting state — pass `change_notes` to annotate what changed."""
    try:
        return await service.update(website_id, payload)
    except WebsiteNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Website not found.") from exc
    except WebsiteConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.delete(
    "/{website_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive (soft-delete) a website",
    responses={404: {"description": "Website not found"}},
)
async def delete_website(
    website_id: uuid.UUID,
    service: WebsiteService = Depends(get_service),
) -> None:
    """Sets status to 'archived' rather than deleting the row, and records
    a final version snapshot — see WebsiteService.delete for why."""
    try:
        await service.delete(website_id)
    except WebsiteNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Website not found.") from exc
