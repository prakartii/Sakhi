"""Data-access layer for mentor_profiles (the mentor directory).

Named MentorRepository (not MentorProfileRepository) to match the
requested repository list; it maps to the MentorProfile model.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MentorAvailability
from app.models.mentor_profile import MentorProfile
from app.repositories.base import BaseRepository

_SEARCH_FIELDS = ("full_name", "bio", "industry_focus")


class MentorRepository(BaseRepository[MentorProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MentorProfile)

    async def list_active(
        self,
        *,
        availability_status: MentorAvailability | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MentorProfile], int]:
        filters: dict[str, object] = {"is_active": True}
        if availability_status is not None:
            filters["availability_status"] = availability_status
        return await self.get_all(filters=filters, limit=limit, offset=offset)

    async def search(
        self,
        query: str,
        *,
        active_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[MentorProfile], int]:
        """Substring search over full_name/bio/industry_focus, active
        mentors only unless active_only=False."""
        filters = {"is_active": True} if active_only else None
        return await self._search(
            query, fields=_SEARCH_FIELDS, filters=filters, limit=limit, offset=offset
        )
