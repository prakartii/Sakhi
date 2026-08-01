"""Unit tests for BaseRepository's shared contract: pagination validation,
filter validation, and the read/write exception-handling split described in
its module docstring. Exercised via BusinessProfile purely as a convenient
concrete model — these tests target BaseRepository's own logic, not
BusinessProfileRepository's.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.business_profile import BusinessProfile
from app.repositories.base import (
    BaseRepository,
    InvalidPaginationError,
    RepositoryError,
)


def _mock_session() -> MagicMock:
    session = MagicMock()
    session.add = MagicMock()
    session.get = AsyncMock(return_value=None)
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = []
    result.scalar_one.return_value = 0
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    return session


def _repo() -> BaseRepository[BusinessProfile]:
    return BaseRepository(_mock_session(), BusinessProfile)


async def test_get_all_rejects_limit_below_one():
    with pytest.raises(InvalidPaginationError):
        await _repo().get_all(limit=0)


async def test_get_all_rejects_limit_above_200():
    with pytest.raises(InvalidPaginationError):
        await _repo().get_all(limit=201)


async def test_get_all_rejects_negative_offset():
    with pytest.raises(InvalidPaginationError):
        await _repo().get_all(offset=-1)


async def test_get_all_rejects_unknown_filter_column():
    with pytest.raises(ValueError, match="no column"):
        await _repo().get_all(filters={"not_a_real_column": 1})


async def test_get_all_accepts_list_value_as_in_clause():
    items, total = await _repo().get_all(filters={"status": ["active", "inactive"]})
    assert items == []
    assert total == 0


async def test_search_requires_at_least_one_field():
    with pytest.raises(ValueError, match="at least one field"):
        await _repo()._search("query", fields=[])


async def test_count_wraps_unexpected_sqlalchemy_error():
    session = _mock_session()
    session.execute.side_effect = SQLAlchemyError("connection lost")
    repo = BaseRepository(session, BusinessProfile)

    with pytest.raises(RepositoryError) as exc_info:
        await repo.count()
    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)


async def test_get_by_id_wraps_unexpected_sqlalchemy_error():
    session = _mock_session()
    session.get.side_effect = SQLAlchemyError("boom")
    repo = BaseRepository(session, BusinessProfile)

    with pytest.raises(RepositoryError):
        await repo.get_by_id(uuid.uuid4())


async def test_create_does_not_catch_integrity_error():
    """Write paths intentionally let IntegrityError propagate unwrapped —
    the service layer owns interpreting it and rolling back."""
    session = _mock_session()
    session.flush.side_effect = IntegrityError("INSERT", {}, Exception("dup key"))
    repo = BaseRepository(session, BusinessProfile)

    with pytest.raises(IntegrityError):
        await repo.create(BusinessProfile())


async def test_create_adds_and_flushes_without_committing():
    session = _mock_session()
    repo = BaseRepository(session, BusinessProfile)
    instance = BusinessProfile()

    result = await repo.create(instance)

    assert result is instance
    session.add.assert_called_once_with(instance)
    session.flush.assert_awaited_once()
    session.commit.assert_not_called()


async def test_update_applies_only_given_fields():
    session = _mock_session()
    repo = BaseRepository(session, BusinessProfile)
    instance = BusinessProfile(business_name="Old")

    result = await repo.update(instance, {"business_name": "New"})

    assert result.business_name == "New"
    session.flush.assert_awaited_once()


async def test_delete_removes_and_flushes():
    session = _mock_session()
    repo = BaseRepository(session, BusinessProfile)
    instance = BusinessProfile()

    await repo.delete(instance)

    session.delete.assert_awaited_once_with(instance)
    session.flush.assert_awaited_once()


async def test_exists_true_when_row_found():
    session = _mock_session()
    session.execute.return_value.scalar_one_or_none.return_value = uuid.uuid4()
    repo = BaseRepository(session, BusinessProfile)

    assert await repo.exists(uuid.uuid4()) is True


async def test_exists_false_when_row_missing():
    assert await _repo().exists(uuid.uuid4()) is False
