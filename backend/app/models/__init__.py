"""SQLAlchemy ORM models mapping to the Supabase schema.

The schema itself already exists in Supabase via the raw SQL migrations in
supabase/migrations/ — every table there has a corresponding model below,
mapped column-for-column, index-for-index, and constraint-for-constraint.
Every model is imported here (not just defined in its own file) for two
reasons:

  1. Alembic's env.py imports this package so Base.metadata is fully
     populated before autogenerate/offline-migration runs.
  2. SQLAlchemy resolves each relationship()'s string class name (and each
     ForeignKey's "table.column" string) lazily, the first time mappers are
     configured — which requires every mapped class to have already been
     imported at least once. Importing them all here, in one place, is what
     makes that guaranteed regardless of which model a caller imports first.

Import order below follows the tables' dependency order (independent
lookups first, deepest child tables last) purely for readability; it has no
functional effect; see business_profile.py for why the actual dependency
graph can be a one-way star without cycles despite the FKs pointing in every
direction.
"""

from app.models.language import Language
from app.models.user import User
from app.models.user_preferences import UserPreferences
from app.models.business_profile import BusinessProfile
from app.models.brand_asset import BrandAsset
from app.models.website import Website
from app.models.website_version import WebsiteVersion
from app.models.voice_log import VoiceLog
from app.models.business_memory import BusinessMemory
from app.models.memory_embedding import MemoryEmbedding
from app.models.conversation_history import ConversationHistory
from app.models.supplier import Supplier
from app.models.inventory import Inventory
from app.models.transaction import Transaction
from app.models.transaction_item import TransactionItem
from app.models.inventory_movement import InventoryMovement
from app.models.government_scheme import GovernmentScheme
from app.models.scheme_match import SchemeMatch
from app.models.opportunity import Opportunity
from app.models.opportunity_match import OpportunityMatch
from app.models.mentor_profile import MentorProfile
from app.models.mentor_match import MentorMatch
from app.models.forecast_history import ForecastHistory
from app.models.notification import Notification
from app.models.social_media_connection import SocialMediaConnection
from app.models.content_calendar_item import ContentCalendarItem
from app.models.scheduled_post import ScheduledPost
from app.models.marketing_analytics_snapshot import MarketingAnalyticsSnapshot
from app.models.marketing_content_analysis import MarketingContentAnalysis

__all__ = [
    "Language",
    "User",
    "UserPreferences",
    "BusinessProfile",
    "BrandAsset",
    "Website",
    "WebsiteVersion",
    "VoiceLog",
    "BusinessMemory",
    "MemoryEmbedding",
    "ConversationHistory",
    "Supplier",
    "Inventory",
    "Transaction",
    "TransactionItem",
    "InventoryMovement",
    "GovernmentScheme",
    "SchemeMatch",
    "Opportunity",
    "OpportunityMatch",
    "MentorProfile",
    "MentorMatch",
    "ForecastHistory",
    "Notification",
    "SocialMediaConnection",
    "ContentCalendarItem",
    "ScheduledPost",
    "MarketingAnalyticsSnapshot",
    "MarketingContentAnalysis",
]
