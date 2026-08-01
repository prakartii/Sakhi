"""Generic async repository: the shared CRUD/pagination/filtering/search
implementation every concrete repository builds on, so that logic exists in
exactly one place instead of being copy-pasted across ten files.

Transaction ownership: create()/update()/delete() only add/flush/delete —
they never commit or roll back. That's deliberate, not an oversight: a
service typically batches several repository calls into one unit of work,
and only the service knows when that unit of work is actually finished, so
only it can correctly decide when to commit or roll back. This preserves
the pattern already established in app/services/business_profile.py.

Exception-handling split — reads vs. writes:
  * Read operations (get_by_id/get_all/exists/count/_search) catch
    SQLAlchemyError and re-raise as RepositoryError. There is no domain
    meaning to attach to a broken SELECT — it's always an infrastructure
    failure, so normalizing it here is safe and removes ten copies of the
    same try/except.
  * Write operations (create/update/delete) deliberately do NOT catch
    IntegrityError. Which constraint fired and what that means for the
    caller (e.g. "this is a duplicate primary business") is business logic
    that only the service layer has enough context to interpret — wrapping
    it here would erase that context instead of preserving it. Services
    remain responsible for catching IntegrityError, rolling back, and
    translating it into a domain-specific exception.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class RepositoryError(Exception):
    """Base class for repository-layer failures raised by read operations."""


class InvalidPaginationError(RepositoryError):
    """limit/offset were outside the allowed range."""


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self.session = session
        self.model = model

    # -- writes -------------------------------------------------------------
    # No try/except, no commit/rollback here — see module docstring.
    async def create(self, instance: ModelType) -> ModelType:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: ModelType, data: Mapping[str, Any]) -> ModelType:
        for field, value in data.items():
            setattr(instance, field, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: ModelType) -> None:
        await self.session.delete(instance)
        await self.session.flush()

    # -- reads ----------------------------------------------------------------
    async def get_by_id(self, id_: uuid.UUID) -> ModelType | None:
        try:
            return await self.session.get(self.model, id_)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                f"Failed to fetch {self.model.__name__} by id={id_!r}"
            ) from exc

    async def exists(self, id_: uuid.UUID) -> bool:
        return await self.exists_by({"id": id_})

    async def exists_by(self, filters: Mapping[str, Any]) -> bool:
        stmt = select(self.model.id).where(*self._build_conditions(filters)).limit(1)
        try:
            result = await self.session.execute(stmt)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                f"Failed to check existence of {self.model.__name__} "
                f"matching {dict(filters)!r}"
            ) from exc
        return result.scalar_one_or_none() is not None

    async def count(self, filters: Mapping[str, Any] | None = None) -> int:
        stmt = select(func.count()).select_from(self.model)
        conditions = self._build_conditions(filters or {})
        if conditions:
            stmt = stmt.where(*conditions)
        try:
            result = await self.session.execute(stmt)
        except SQLAlchemyError as exc:
            raise RepositoryError(
                f"Failed to count {self.model.__name__} rows"
            ) from exc
        return result.scalar_one()

    async def get_all(
        self,
        *,
        filters: Mapping[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
        order_by: ColumnElement[Any] | None = None,
    ) -> tuple[list[ModelType], int]:
        """Paginated, optionally filtered listing.

        `filters` is a simple {column_name: value} equality map; a list/
        tuple/set value is turned into an IN(...) clause instead of `=`.
        This is deliberately mechanical (no domain interpretation of what a
        filter *means*) — deciding which filters to pass is the caller's
        job.
        """
        self._validate_pagination(limit, offset)
        conditions = self._build_conditions(filters or {})
        total = await self.count(filters)

        stmt = select(self.model)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(
            order_by if order_by is not None else self._default_order()
        )
        stmt = stmt.limit(limit).offset(offset)

        try:
            result = await self.session.execute(stmt)
        except SQLAlchemyError as exc:
            raise RepositoryError(f"Failed to list {self.model.__name__} rows") from exc
        return list(result.scalars().all()), total

    async def _search(
        self,
        query: str,
        *,
        fields: Sequence[str],
        filters: Mapping[str, Any] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ModelType], int]:
        """Case-insensitive substring search across `fields` (OR'd
        together), further narrowed by `filters` (AND'd equality/membership
        conditions). Protected: concrete repositories expose this under
        their own public `search()` method that pins down which columns are
        searchable for that entity — see e.g. business_profile.py.
        """
        self._validate_pagination(limit, offset)
        if not fields:
            raise ValueError("search requires at least one field to search")

        pattern = f"%{query}%"
        text_conditions = [
            getattr(self.model, field).ilike(pattern) for field in fields
        ]
        equality_conditions = self._build_conditions(filters or {})
        or_clause = or_(*text_conditions)

        count_stmt = (
            select(func.count())
            .select_from(self.model)
            .where(or_clause, *equality_conditions)
        )
        list_stmt = (
            select(self.model)
            .where(or_clause, *equality_conditions)
            .order_by(self._default_order())
            .limit(limit)
            .offset(offset)
        )
        try:
            total = (await self.session.execute(count_stmt)).scalar_one()
            rows = (await self.session.execute(list_stmt)).scalars().all()
        except SQLAlchemyError as exc:
            raise RepositoryError(
                f"Failed to search {self.model.__name__} rows"
            ) from exc
        return list(rows), total

    # -- internal helpers -----------------------------------------------------
    def _build_conditions(
        self, filters: Mapping[str, Any]
    ) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        for field, value in filters.items():
            try:
                column = getattr(self.model, field)
            except AttributeError as exc:
                raise ValueError(
                    f"{self.model.__name__} has no column '{field}'"
                ) from exc
            if isinstance(value, list | tuple | set | frozenset):
                conditions.append(column.in_(value))
            else:
                conditions.append(column == value)
        return conditions

    def _default_order(self) -> ColumnElement[Any]:
        created_at = getattr(self.model, "created_at", None)
        return created_at.desc() if created_at is not None else self.model.id

    @staticmethod
    def _validate_pagination(limit: int, offset: int) -> None:
        if not 1 <= limit <= 200:
            raise InvalidPaginationError("limit must be between 1 and 200")
        if offset < 0:
            raise InvalidPaginationError("offset must be >= 0")
