"""Aggregates all v1 endpoint routers into a single api_router mounted by
app.main under settings.API_V1_PREFIX.

Register each feature's router here as it's implemented, e.g.:

    from app.api.v1.endpoints import business_profiles
    api_router.include_router(
        business_profiles.router,
        prefix="/business-profiles",
        tags=["business-profiles"],
    )
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    advisor,
    brand_assets,
    business_memories,
    business_profiles,
    content_calendar_items,
    content_generation,
    inventory,
    marketing_analytics_snapshots,
    marketing_studio,
    mentors,
    notifications,
    onboarding,
    scheduled_posts,
    schemes,
    social_media_connections,
    transactions,
    voice,
    website_generation,
    website_public,
    websites,
)

api_router = APIRouter()

api_router.include_router(
    business_profiles.router,
    prefix="/business-profiles",
    tags=["business-profiles"],
)

api_router.include_router(
    onboarding.router,
    prefix="/onboarding",
    tags=["onboarding"],
)

api_router.include_router(
    business_memories.router,
    prefix="/business-memories",
    tags=["business-memories"],
)

api_router.include_router(
    brand_assets.router,
    prefix="/brand-assets",
    tags=["brand-assets"],
)

api_router.include_router(
    websites.router,
    prefix="/websites",
    tags=["websites"],
)

api_router.include_router(
    website_generation.router,
    prefix="/websites",
    tags=["websites", "website-ai"],
)

api_router.include_router(
    website_public.router,
    prefix="/public/websites",
    tags=["public"],
)

api_router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["transactions"],
)

api_router.include_router(
    inventory.router,
    prefix="/inventory",
    tags=["inventory"],
)

api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["notifications"],
)

api_router.include_router(
    social_media_connections.router,
    prefix="/social-connections",
    tags=["social-media-connections"],
)

api_router.include_router(
    content_calendar_items.router,
    prefix="/content-calendar",
    tags=["content-calendar"],
)

api_router.include_router(
    content_generation.router,
    prefix="/content-calendar",
    tags=["content-calendar", "content-ai"],
)

api_router.include_router(
    scheduled_posts.router,
    prefix="/scheduled-posts",
    tags=["scheduled-posts"],
)

api_router.include_router(
    marketing_analytics_snapshots.router,
    prefix="/marketing-analytics",
    tags=["marketing-analytics"],
)

api_router.include_router(
    marketing_studio.router,
    prefix="/marketing-studio",
    tags=["marketing-studio"],
)

api_router.include_router(
    schemes.router,
    prefix="/schemes",
    tags=["schemes"],
)

api_router.include_router(
    mentors.router,
    prefix="/mentors",
    tags=["mentors"],
)

api_router.include_router(
    advisor.router,
    prefix="/advisor",
    tags=["advisor"],
)

api_router.include_router(
    voice.router,
    prefix="/voice",
    tags=["voice"],
)
