"""Shared FastAPI dependencies, imported by routers as `Depends(...)`.

Routers should import from here rather than reaching into app.db.session or
app.repositories directly, so the DI surface stays stable even if the
underlying session/repository construction changes. Each get_*_repository
below is a thin factory over the request-scoped AsyncSession — routers or
services can `Depends()` on a repository directly, and tests can override
any single one via app.dependency_overrides without touching the rest.
Repository modules themselves stay framework-agnostic (no FastAPI import in
app/repositories/) — that coupling lives here instead.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supabase_auth import CurrentUser, get_current_user
from app.db.session import get_db as get_db_session
from app.models.user import User
from app.repositories.brand_asset import BrandAssetRepository
from app.repositories.business_memory import BusinessMemoryRepository
from app.repositories.business_profile import BusinessProfileRepository
from app.repositories.content_calendar_item import ContentCalendarItemRepository
from app.repositories.conversation_history import ConversationHistoryRepository
from app.repositories.government_scheme import GovernmentSchemeRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.inventory_movement import InventoryMovementRepository
from app.repositories.marketing_analytics_snapshot import (
    MarketingAnalyticsSnapshotRepository,
)
from app.repositories.mentor import MentorRepository
from app.repositories.notification import NotificationRepository
from app.repositories.opportunity import OpportunityRepository
from app.repositories.scheduled_post import ScheduledPostRepository
from app.repositories.social_media_connection import SocialMediaConnectionRepository
from app.repositories.supplier import SupplierRepository
from app.repositories.transaction import TransactionRepository
from app.repositories.voice_log import VoiceLogRepository
from app.repositories.website import WebsiteRepository
from app.repositories.website_version import WebsiteVersionRepository
from app.services.user import UserService

__all__ = [
    "get_db_session",
    "get_current_user",
    "get_current_app_user",
    "get_business_profile_repository",
    "get_brand_asset_repository",
    "get_website_repository",
    "get_website_version_repository",
    "get_transaction_repository",
    "get_inventory_repository",
    "get_inventory_movement_repository",
    "get_supplier_repository",
    "get_voice_log_repository",
    "get_conversation_history_repository",
    "get_business_memory_repository",
    "get_government_scheme_repository",
    "get_opportunity_repository",
    "get_mentor_repository",
    "get_notification_repository",
    "get_social_media_connection_repository",
    "get_content_calendar_item_repository",
    "get_scheduled_post_repository",
    "get_marketing_analytics_snapshot_repository",
]


async def get_current_app_user(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Verified Supabase identity, mirrored into public.users if this is the
    first request seen for that id. Use this (instead of get_current_user)
    wherever an endpoint needs a real users.id foreign key, not just proof
    of a valid session."""
    return await UserService(db).ensure_local_user(current)


def get_business_profile_repository(
    db: AsyncSession = Depends(get_db_session),
) -> BusinessProfileRepository:
    return BusinessProfileRepository(db)


def get_brand_asset_repository(
    db: AsyncSession = Depends(get_db_session),
) -> BrandAssetRepository:
    return BrandAssetRepository(db)


def get_website_repository(
    db: AsyncSession = Depends(get_db_session),
) -> WebsiteRepository:
    return WebsiteRepository(db)


def get_website_version_repository(
    db: AsyncSession = Depends(get_db_session),
) -> WebsiteVersionRepository:
    return WebsiteVersionRepository(db)


def get_transaction_repository(
    db: AsyncSession = Depends(get_db_session),
) -> TransactionRepository:
    return TransactionRepository(db)


def get_inventory_repository(
    db: AsyncSession = Depends(get_db_session),
) -> InventoryRepository:
    return InventoryRepository(db)


def get_inventory_movement_repository(
    db: AsyncSession = Depends(get_db_session),
) -> InventoryMovementRepository:
    return InventoryMovementRepository(db)


def get_supplier_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SupplierRepository:
    return SupplierRepository(db)


def get_voice_log_repository(
    db: AsyncSession = Depends(get_db_session),
) -> VoiceLogRepository:
    return VoiceLogRepository(db)


def get_conversation_history_repository(
    db: AsyncSession = Depends(get_db_session),
) -> ConversationHistoryRepository:
    return ConversationHistoryRepository(db)


def get_business_memory_repository(
    db: AsyncSession = Depends(get_db_session),
) -> BusinessMemoryRepository:
    return BusinessMemoryRepository(db)


def get_government_scheme_repository(
    db: AsyncSession = Depends(get_db_session),
) -> GovernmentSchemeRepository:
    return GovernmentSchemeRepository(db)


def get_opportunity_repository(
    db: AsyncSession = Depends(get_db_session),
) -> OpportunityRepository:
    return OpportunityRepository(db)


def get_mentor_repository(
    db: AsyncSession = Depends(get_db_session),
) -> MentorRepository:
    return MentorRepository(db)


def get_notification_repository(
    db: AsyncSession = Depends(get_db_session),
) -> NotificationRepository:
    return NotificationRepository(db)


def get_social_media_connection_repository(
    db: AsyncSession = Depends(get_db_session),
) -> SocialMediaConnectionRepository:
    return SocialMediaConnectionRepository(db)


def get_content_calendar_item_repository(
    db: AsyncSession = Depends(get_db_session),
) -> ContentCalendarItemRepository:
    return ContentCalendarItemRepository(db)


def get_scheduled_post_repository(
    db: AsyncSession = Depends(get_db_session),
) -> ScheduledPostRepository:
    return ScheduledPostRepository(db)


def get_marketing_analytics_snapshot_repository(
    db: AsyncSession = Depends(get_db_session),
) -> MarketingAnalyticsSnapshotRepository:
    return MarketingAnalyticsSnapshotRepository(db)
