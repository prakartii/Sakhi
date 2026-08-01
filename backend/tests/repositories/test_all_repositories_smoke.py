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
