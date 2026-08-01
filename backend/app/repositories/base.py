"""Generic repository base. Concrete repositories subclass this per model and
add query methods as business logic is implemented — this class deliberately
stops at construction, no query methods yet.
"""

from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self.session = session
        self.model = model
