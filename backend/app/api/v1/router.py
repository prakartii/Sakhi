"""Aggregates all v1 endpoint routers into a single api_router mounted by
app.main under settings.API_V1_PREFIX.

Empty by design — no CRUD endpoints exist yet. As each feature's endpoints
are implemented under app.api.v1.endpoints, register them here, e.g.:

    from app.api.v1.endpoints import business_profiles
    api_router.include_router(
        business_profiles.router,
        prefix="/business-profiles",
        tags=["business-profiles"],
    )
"""

from fastapi import APIRouter

api_router = APIRouter()
