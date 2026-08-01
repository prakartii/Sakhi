"""Keeps public.users in sync with Supabase's auth.users.

Supabase Auth owns signup/login and writes to auth.users directly; this app
never touches that table. app.models.user.User (and everything that
foreign-keys to it — business_profiles, notifications, voice_logs, ...)
needs a matching public.users row to exist first. ensure_local_user() is
called on every authenticated request and creates that row the first time a
given Supabase user id is seen, so the rest of the app can treat
current_user.id as a valid users.id without a separate signup-sync step.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supabase_auth import CurrentUser
from app.models.user import User
from app.repositories.user import UserRepository


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserRepository(session)

    async def ensure_local_user(self, current: CurrentUser) -> User:
        existing = await self._repo.get_by_id(current.id)
        if existing is not None:
            return existing
        user = User(
            id=current.id,
            email=current.email or f"{current.id}@unknown.local",
            full_name=current.full_name,
        )
        await self._repo.create(user)
        await self._session.commit()
        return user
