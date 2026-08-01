"""Business Profile module endpoints: registration/identity CRUD plus the
onboarding/growth-workflow fields (owner, description, stage, socials) and
an onboarding-completion check.

No authentication yet: user_id is supplied explicitly by the caller
(request body on create, required query param on list) instead of being
derived from a session. That's a deliberate, temporary gap — it goes away
once auth is implemented, not an oversight.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.models.enums import BusinessStatus
from app.schemas.business_profile import (
    BusinessProfileCreate,
    BusinessProfileListResponse,
    BusinessProfileOnboardingStatus,
    BusinessProfilePut,
    BusinessProfileRead,
    BusinessProfileUpdate,
)
from app.services.business_profile import (
    BusinessProfileConflictError,
    BusinessProfileNotFoundError,
    BusinessProfileService,
    InvalidReferenceError,
)

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
    service: BusinessProfileService = Depends(get_service),
) -> BusinessProfileRead:
    """Create a business profile for a user.

    `is_primary` defaults to true; a user may have at most one primary
    business profile (enforced by the database) — creating a second
    primary profile returns 409. Onboarding fields (owner_name,
    business_description, target_audience, products_or_services,
    business_stage, and the social/website links) are all optional at
    creation time; use PATCH or PUT to fill them in later, and
    GET .../onboarding-status to check what's still missing.
    """
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
    user_id: uuid.UUID = Query(
        ...,
        description="Owning user id (temporary — replaced by session-derived "
        "scoping once auth exists).",
    ),
    status_filter: BusinessStatus | None = Query(
        None, alias="status", description="Filter by lifecycle status."
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: BusinessProfileService = Depends(get_service),
) -> BusinessProfileListResponse:
    """List business profiles owned by a given user, newest first."""
    items, total = await service.list(
        user_id, status=status_filter, limit=limit, offset=offset
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
