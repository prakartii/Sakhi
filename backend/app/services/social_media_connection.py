"""Business logic for Social Media Connections.

Owns the transaction boundary (commit/rollback) around each use case and
translates database-level failures into domain exceptions the API layer
maps to HTTP status codes — routers never see SQLAlchemy exceptions or
raw token values directly.

Access-token handling is centralized here on purpose: connect() and
refresh_token() are the only two places that write access_token/
refresh_token, and both funnel through _token_fields() below. That's the
single choke point the task asked for — swapping in an encrypted-at-rest
column, a KMS-backed secret store, or a different provider's token shape
later is a change to this one function, not to every call site, and
routers/schemas never touch a token value at all (SocialMediaConnectionRead
never includes one — see app/schemas/social_media_connection.py).

This module never calls a platform API — see connect()/refresh_token()/
sync_metadata()'s docstrings for what each one actually does instead.

Uses `from __future__ import annotations` for the same reason as
WebsiteService/InventoryService: this class has a method literally named
`list`, which would otherwise shadow the `list` builtin for any later
method's own `list[...]` return annotation once the class body finishes
executing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SocialConnectionStatus, SocialMediaPlatform
from app.models.social_media_connection import SocialMediaConnection
from app.repositories.social_media_connection import SocialMediaConnectionRepository
from app.schemas.social_media_connection import (
    RefreshTokenRequest,
    SocialMediaConnectionCreate,
    SyncMetadataRequest,
)


class SocialMediaConnectionNotFoundError(Exception):
    """No social_media_connections row exists for the given id."""


class InvalidReferenceError(Exception):
    """The referenced business_profile_id does not exist."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "social_media_connections_business_profile_id_fkey" in message:
        return InvalidReferenceError(
            "business_profile_id does not reference an existing business profile."
        )
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500. Notably this
    # includes the unique(business_profile_id, platform) constraint, which
    # connect() avoids ever hitting by checking first — see below.
    return exc


def _token_fields(
    *,
    access_token: str,
    refresh_token: str | None,
    token_expiry: datetime | None,
) -> dict[str, object]:
    """The one place a token payload becomes column values. See module
    docstring for why this exists as a single function."""
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expiry": token_expiry,
    }


class SocialMediaConnectionService:
    def __init__(
        self,
        session: AsyncSession,
        repository: SocialMediaConnectionRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or SocialMediaConnectionRepository(session)

    async def connect(
        self, payload: SocialMediaConnectionCreate
    ) -> SocialMediaConnection:
        """Connects a platform for a business. Idempotent per
        (business_profile_id, platform): if that pair is already connected
        (or was, and is now disconnected/expired/error), this updates the
        existing row with fresh tokens and metadata and sets status back to
        connected, rather than failing on the table's unique constraint or
        accumulating a duplicate row for the same platform.
        """
        existing = await self._repo.get_by_business_profile_and_platform(
            payload.business_profile_id, payload.platform
        )
        try:
            if existing is not None:
                data = {
                    "account_name": payload.account_name,
                    "account_id": payload.account_id,
                    "profile_url": payload.profile_url,
                    "connection_status": SocialConnectionStatus.CONNECTED,
                    **_token_fields(
                        access_token=payload.access_token,
                        refresh_token=payload.refresh_token,
                        token_expiry=payload.token_expiry,
                    ),
                }
                await self._repo.update(existing, data)
                await self._session.commit()
                return existing

            connection = SocialMediaConnection(
                business_profile_id=payload.business_profile_id,
                platform=payload.platform,
                account_name=payload.account_name,
                account_id=payload.account_id,
                profile_url=payload.profile_url,
                connection_status=SocialConnectionStatus.CONNECTED,
                **_token_fields(
                    access_token=payload.access_token,
                    refresh_token=payload.refresh_token,
                    token_expiry=payload.token_expiry,
                ),
            )
            await self._repo.create(connection)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return connection

    async def get(self, connection_id: uuid.UUID) -> SocialMediaConnection:
        connection = await self._repo.get_by_id(connection_id)
        if connection is None:
            raise SocialMediaConnectionNotFoundError(str(connection_id))
        return connection

    async def list(
        self,
        business_profile_id: uuid.UUID,
        *,
        platform: SocialMediaPlatform | None = None,
        connection_status: SocialConnectionStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[SocialMediaConnection], int]:
        return await self._repo.list_by_business_profile(
            business_profile_id,
            platform=platform,
            connection_status=connection_status,
            limit=limit,
            offset=offset,
        )

    async def disconnect(self, connection_id: uuid.UUID) -> SocialMediaConnection:
        """Sets connection_status to disconnected and clears the stored
        tokens. A disconnected connection has no reason to keep holding
        credentials it's no longer meant to use — reconnecting later
        (connect()) supplies fresh tokens and flips status back to
        connected."""
        connection = await self.get(connection_id)
        await self._repo.update(
            connection,
            {
                "connection_status": SocialConnectionStatus.DISCONNECTED,
                "access_token": None,
                "refresh_token": None,
                "token_expiry": None,
            },
        )
        await self._session.commit()
        return connection

    async def refresh_token(
        self, connection_id: uuid.UUID, payload: RefreshTokenRequest
    ) -> SocialMediaConnection:
        """Records a token this module did not obtain itself — no platform
        API is called here. The caller (a future OAuth-handling module, or
        a manual operation) already has a new access_token from the
        provider's own refresh flow; this just persists it and marks the
        connection connected again, e.g. clearing a prior `expired`/`error`
        status."""
        connection = await self.get(connection_id)
        data = {
            "connection_status": SocialConnectionStatus.CONNECTED,
            **_token_fields(
                access_token=payload.access_token,
                refresh_token=payload.refresh_token,
                token_expiry=payload.token_expiry,
            ),
        }
        await self._repo.update(connection, data)
        await self._session.commit()
        return connection

    async def sync_metadata(
        self, connection_id: uuid.UUID, payload: SyncMetadataRequest
    ) -> SocialMediaConnection:
        """Records account metadata this module did not fetch itself — no
        platform API is called here. The caller already has updated
        account_name/account_id/profile_url from the provider; this
        persists whichever of those were actually supplied and stamps
        last_sync, regardless of whether any field changed."""
        connection = await self.get(connection_id)
        data = payload.model_dump(exclude_unset=True)
        data["last_sync"] = datetime.now(timezone.utc)
        await self._repo.update(connection, data)
        await self._session.commit()
        return connection
