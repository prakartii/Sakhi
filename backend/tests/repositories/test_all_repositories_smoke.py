"""Cross-repository verification: confirms every repository binds to a
real SQLAlchemy model and that their generic CRUD/search methods execute
against that model without raising. In particular, this catches a typo'd
column name in any repo's hardcoded search fields / order_by / filters —
that would surface as AttributeError/ValueError here, since getattr(model,
field) is evaluated during statement construction regardless of what the
(mocked) session returns.

The session is mocked throughout, so this validates statement construction
against the real mapped models without needing a live database connection.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import PublishingStatus, SocialMediaPlatform
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

REPOSITORY_TABLES = {
    BusinessProfileRepository: "business_profiles",
    BrandAssetRepository: "brand_assets",
    WebsiteRepository: "websites",
    WebsiteVersionRepository: "website_versions",
    TransactionRepository: "transactions",
    InventoryRepository: "inventory",
    InventoryMovementRepository: "inventory_movements",
    SupplierRepository: "suppliers",
    VoiceLogRepository: "voice_logs",
    ConversationHistoryRepository: "conversation_history",
    BusinessMemoryRepository: "business_memory",
    GovernmentSchemeRepository: "government_schemes",
    OpportunityRepository: "opportunities",
    MentorRepository: "mentor_profiles",
    NotificationRepository: "notifications",
    SocialMediaConnectionRepository: "social_media_connections",
    ContentCalendarItemRepository: "content_calendar_items",
}


def _mock_session() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.get = AsyncMock(return_value=None)
    session.delete = AsyncMock()
    session.flush = AsyncMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    result.scalar_one.return_value = 0
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    return session


@pytest.mark.parametrize("repo_cls,expected_table", list(REPOSITORY_TABLES.items()))
def test_repository_binds_to_the_correct_table(repo_cls, expected_table):
    repo = repo_cls(_mock_session())
    assert repo.model.__tablename__ == expected_table


@pytest.mark.parametrize("repo_cls", list(REPOSITORY_TABLES), ids=lambda c: c.__name__)
async def test_generic_crud_contract_executes_against_the_real_model(repo_cls):
    session = _mock_session()
    repo = repo_cls(session)

    assert await repo.get_by_id(uuid.uuid4()) is None
    assert await repo.exists(uuid.uuid4()) is False
    assert await repo.count() == 0

    items, total = await repo.get_all()
    assert items == []
    assert total == 0

    instance = repo.model()
    created = await repo.create(instance)
    assert created is instance
    session.add.assert_called_once_with(instance)

    updated = await repo.update(instance, {})
    assert updated is instance

    await repo.delete(instance)
    session.delete.assert_awaited_once_with(instance)


@pytest.mark.parametrize("repo_cls", list(REPOSITORY_TABLES), ids=lambda c: c.__name__)
async def test_search_columns_are_real_and_query_executes(repo_cls):
    """Exercises each repo's hardcoded search fields via getattr() against
    the real model."""
    repo = repo_cls(_mock_session())
    items, total = await repo.search("test query")
    assert items == []
    assert total == 0


async def test_business_profile_list_by_user_filters_by_user_id():
    session = _mock_session()
    repo = BusinessProfileRepository(session)

    await repo.list_by_user(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "business_profiles.user_id" in rendered


async def test_brand_asset_list_by_business_profile_filters_by_business_profile_id():
    session = _mock_session()
    repo = BrandAssetRepository(session)

    await repo.list_by_business_profile(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "brand_assets.business_profile_id" in rendered


async def test_website_list_by_business_profile_filters_by_business_profile_id():
    session = _mock_session()
    repo = WebsiteRepository(session)

    await repo.list_by_business_profile(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "websites.business_profile_id" in rendered


async def test_website_version_list_by_website_orders_by_version_desc():
    session = _mock_session()
    repo = WebsiteVersionRepository(session)

    await repo.list_by_website(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "ORDER BY website_versions.version_number DESC" in rendered


async def test_transaction_list_by_business_profile_orders_by_date():
    session = _mock_session()
    repo = TransactionRepository(session)

    await repo.list_by_business_profile(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "transaction_date" in rendered


async def test_government_scheme_list_active_filters_is_active():
    session = _mock_session()
    repo = GovernmentSchemeRepository(session)

    await repo.list_active()

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "is_active" in rendered


async def test_notification_list_by_user_filters_user_id():
    session = _mock_session()
    repo = NotificationRepository(session)

    await repo.list_by_user(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "notifications.user_id" in rendered


async def test_social_media_connection_list_by_business_profile_filters_business_profile_id():
    session = _mock_session()
    repo = SocialMediaConnectionRepository(session)

    await repo.list_by_business_profile(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "social_media_connections.business_profile_id" in rendered


async def test_social_media_connection_get_by_business_profile_and_platform_filters_both():
    session = _mock_session()
    repo = SocialMediaConnectionRepository(session)

    await repo.get_by_business_profile_and_platform(
        uuid.uuid4(), SocialMediaPlatform.INSTAGRAM
    )

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "social_media_connections.business_profile_id" in rendered
    assert "social_media_connections.platform" in rendered


async def test_conversation_history_list_by_session_orders_chronologically():
    session = _mock_session()
    repo = ConversationHistoryRepository(session)

    await repo.list_by_session(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "ORDER BY conversation_history.created_at" in rendered
    assert "DESC" not in rendered.split("ORDER BY")[1]


async def test_inventory_list_by_business_profile_filters_category_and_supplier():
    session = _mock_session()
    repo = InventoryRepository(session)

    await repo.list_by_business_profile(
        uuid.uuid4(), category="Textiles", supplier_id=uuid.uuid4()
    )

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "inventory.category" in rendered
    assert "inventory.supplier_id" in rendered


async def test_inventory_search_combines_text_and_equality_filters():
    session = _mock_session()
    repo = InventoryRepository(session)

    await repo.search("scarf", business_profile_id=uuid.uuid4(), category="Textiles")

    rendered = str(session.execute.call_args_list[-1].args[0])
    # str() on a statement uses SQLAlchemy's generic compiler (no dialect
    # bound), which renders .ilike() as `lower(x) LIKE lower(y)` rather
    # than literal ILIKE — that's the actual, correct compiled form here,
    # not a stand-in for it.
    assert "lower(inventory.item_name) like" in rendered.lower()
    assert "inventory.category" in rendered


async def test_inventory_list_low_stock_filters_quantity_and_reorder_level():
    session = _mock_session()
    repo = InventoryRepository(session)

    await repo.list_low_stock(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "inventory.reorder_level" in rendered
    assert "inventory.current_quantity" in rendered


async def test_inventory_list_out_of_stock_filters_current_quantity():
    session = _mock_session()
    repo = InventoryRepository(session)

    await repo.list_out_of_stock(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "inventory.current_quantity" in rendered


async def test_inventory_get_summary_executes_an_aggregate_query():
    session = _mock_session()
    session.execute.return_value.one.return_value = MagicMock(
        total_products=0, total_stock_value=0, low_stock_count=0, out_of_stock_count=0
    )
    repo = InventoryRepository(session)

    summary = await repo.get_summary(uuid.uuid4())

    assert summary == {
        "total_products": 0,
        "total_stock_value": 0.0,
        "low_stock_count": 0,
        "out_of_stock_count": 0,
    }
    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "count" in rendered.lower()
    assert "sum" in rendered.lower()


async def test_inventory_deactivate_sets_is_active_false_and_flushes():
    session = _mock_session()
    repo = InventoryRepository(session)
    item = repo.model(is_active=True)

    result = await repo.deactivate(item)

    assert result.is_active is False
    session.flush.assert_awaited_once()


async def test_supplier_list_by_business_profile_filters_by_business_profile_id():
    session = _mock_session()
    repo = SupplierRepository(session)

    await repo.list_by_business_profile(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "suppliers.business_profile_id" in rendered


async def test_inventory_movement_list_by_inventory_orders_by_movement_date_desc():
    session = _mock_session()
    repo = InventoryMovementRepository(session)

    await repo.list_by_inventory(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "ORDER BY inventory_movements.movement_date DESC" in rendered


async def test_content_calendar_item_list_by_business_profile_filters_business_profile_id():
    session = _mock_session()
    repo = ContentCalendarItemRepository(session)

    await repo.list_by_business_profile(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "content_calendar_items.business_profile_id" in rendered


async def test_content_calendar_item_list_by_date_range_filters_scheduled_datetime():
    from datetime import datetime, timezone

    session = _mock_session()
    repo = ContentCalendarItemRepository(session)

    await repo.list_by_date_range(
        uuid.uuid4(),
        start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end=datetime(2026, 2, 1, tzinfo=timezone.utc),
        platform=SocialMediaPlatform.INSTAGRAM,
    )

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "content_calendar_items.scheduled_datetime" in rendered
    assert "content_calendar_items.platform" in rendered


# ScheduledPostRepository isn't in REPOSITORY_TABLES above (and so doesn't
# go through the generic parametrized create/get_by_id/update/delete/
# search loop): it has no search() — see that repository's module
# docstring for why — so it's exercised directly here instead, covering
# the same generic contract by hand plus its three list methods.


async def test_scheduled_post_binds_to_the_correct_table():
    repo = ScheduledPostRepository(_mock_session())
    assert repo.model.__tablename__ == "scheduled_posts"


async def test_scheduled_post_generic_crud_contract_executes_against_the_real_model():
    session = _mock_session()
    repo = ScheduledPostRepository(session)

    assert await repo.get_by_id(uuid.uuid4()) is None
    assert await repo.exists(uuid.uuid4()) is False
    assert await repo.count() == 0

    items, total = await repo.get_all()
    assert items == []
    assert total == 0

    instance = repo.model()
    created = await repo.create(instance)
    assert created is instance
    session.add.assert_called_once_with(instance)

    updated = await repo.update(instance, {})
    assert updated is instance

    await repo.delete(instance)
    session.delete.assert_awaited_once_with(instance)


async def test_scheduled_post_list_by_business_profile_filters_business_profile_id():
    session = _mock_session()
    repo = ScheduledPostRepository(session)

    await repo.list_by_business_profile(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "scheduled_posts.business_profile_id" in rendered


async def test_scheduled_post_list_queue_filters_to_queued_and_publishing():
    session = _mock_session()
    repo = ScheduledPostRepository(session)

    await repo.list_queue(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "scheduled_posts.publishing_status IN" in rendered


async def test_scheduled_post_list_history_defaults_to_resolved_statuses_ordered_desc():
    session = _mock_session()
    repo = ScheduledPostRepository(session)

    await repo.list_history(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "scheduled_posts.publishing_status IN" in rendered
    assert "ORDER BY scheduled_posts.updated_at DESC" in rendered


async def test_scheduled_post_list_history_narrows_to_one_status_when_given():
    session = _mock_session()
    repo = ScheduledPostRepository(session)

    await repo.list_history(uuid.uuid4(), publishing_status=PublishingStatus.FAILED)

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "scheduled_posts.publishing_status IN" in rendered


# MarketingAnalyticsSnapshotRepository isn't in REPOSITORY_TABLES above for
# the same reason ScheduledPostRepository isn't: no search() — see that
# repository's module docstring for why — so it's exercised directly here
# too, covering the generic contract by hand plus its three aggregate/
# lookup methods.


async def test_marketing_analytics_snapshot_binds_to_the_correct_table():
    repo = MarketingAnalyticsSnapshotRepository(_mock_session())
    assert repo.model.__tablename__ == "marketing_analytics_snapshots"


async def test_marketing_analytics_snapshot_generic_crud_contract_executes_against_the_real_model():
    session = _mock_session()
    repo = MarketingAnalyticsSnapshotRepository(session)

    assert await repo.get_by_id(uuid.uuid4()) is None
    assert await repo.exists(uuid.uuid4()) is False
    assert await repo.count() == 0

    items, total = await repo.get_all()
    assert items == []
    assert total == 0

    instance = repo.model()
    created = await repo.create(instance)
    assert created is instance
    session.add.assert_called_once_with(instance)

    updated = await repo.update(instance, {})
    assert updated is instance

    await repo.delete(instance)
    session.delete.assert_awaited_once_with(instance)


async def test_marketing_analytics_snapshot_aggregate_by_bucket_groups_by_date_trunc():
    from datetime import datetime, timezone

    session = _mock_session()
    repo = MarketingAnalyticsSnapshotRepository(session)

    await repo.aggregate_by_bucket(
        uuid.uuid4(),
        bucket="day",
        start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "date_trunc" in rendered.lower()
    assert "marketing_analytics_snapshots.business_profile_id" in rendered
    assert "marketing_analytics_snapshots.captured_at" in rendered
    assert "sum(marketing_analytics_snapshots.reach)" in rendered.lower()
    assert "avg(marketing_analytics_snapshots.followers)" in rendered.lower()
    assert "group by" in rendered.lower()


async def test_marketing_analytics_snapshot_aggregate_by_bucket_filters_by_social_connection():
    from datetime import datetime, timezone

    session = _mock_session()
    repo = MarketingAnalyticsSnapshotRepository(session)

    await repo.aggregate_by_bucket(
        uuid.uuid4(),
        bucket="week",
        start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end=datetime(2026, 2, 1, tzinfo=timezone.utc),
        social_connection_id=uuid.uuid4(),
    )

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "marketing_analytics_snapshots.social_connection_id" in rendered


async def test_marketing_analytics_snapshot_aggregate_period_has_no_group_by():
    from datetime import datetime, timezone

    session = _mock_session()
    repo = MarketingAnalyticsSnapshotRepository(session)

    await repo.aggregate_period(
        uuid.uuid4(),
        start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "group by" not in rendered.lower()
    assert "coalesce(sum(marketing_analytics_snapshots.engagement)" in rendered.lower()


async def test_marketing_analytics_snapshot_get_latest_orders_by_captured_at_desc():
    session = _mock_session()
    repo = MarketingAnalyticsSnapshotRepository(session)

    await repo.get_latest(uuid.uuid4())

    rendered = str(session.execute.call_args_list[-1].args[0])
    assert "ORDER BY marketing_analytics_snapshots.captured_at DESC" in rendered
