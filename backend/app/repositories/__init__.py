"""Data-access layer: one repository per aggregate, wrapping the
SQLAlchemy queries a service needs. Services depend on repositories, never
on AsyncSession directly, so persistence details stay swappable and
mockable in tests.

All concrete repositories share the generic CRUD/pagination/filtering/
search implementation in base.py (BaseRepository) — see that module's
docstring for the transaction-ownership and exception-handling contract
every repository here follows.
"""

from app.repositories.base import (
    BaseRepository,
    InvalidPaginationError,
    RepositoryError,
)
from app.repositories.brand_asset import BrandAssetRepository
from app.repositories.business_memory import BusinessMemoryRepository
from app.repositories.business_profile import BusinessProfileRepository
from app.repositories.conversation_history import ConversationHistoryRepository
from app.repositories.government_scheme import GovernmentSchemeRepository
from app.repositories.inventory import InventoryRepository
from app.repositories.inventory_movement import InventoryMovementRepository
from app.repositories.mentor import MentorRepository
from app.repositories.notification import NotificationRepository
from app.repositories.opportunity import OpportunityRepository
from app.repositories.supplier import SupplierRepository
from app.repositories.transaction import TransactionRepository
from app.repositories.voice_log import VoiceLogRepository
from app.repositories.website import WebsiteRepository
from app.repositories.website_version import WebsiteVersionRepository

__all__ = [
    "BaseRepository",
    "RepositoryError",
    "InvalidPaginationError",
    "BusinessProfileRepository",
    "BrandAssetRepository",
    "WebsiteRepository",
    "WebsiteVersionRepository",
    "TransactionRepository",
    "InventoryRepository",
    "InventoryMovementRepository",
    "SupplierRepository",
    "VoiceLogRepository",
    "ConversationHistoryRepository",
    "BusinessMemoryRepository",
    "GovernmentSchemeRepository",
    "OpportunityRepository",
    "MentorRepository",
    "NotificationRepository",
]
