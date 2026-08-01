"""Unit tests for SocialMediaConnectionService. Both the repository and the
DB session are faked/mocked — no database connection is used or required.
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import SocialConnectionStatus, SocialMediaPlatform
from app.models.social_media_connection import SocialMediaConnection
from app.schemas.social_media_connection import (
    RefreshTokenRequest,
    SocialMediaConnectionCreate,
    SyncMetadataRequest,
)
from app.services.social_media_connection import (
    InvalidReferenceError,
    SocialMediaConnectionNotFoundError,
    SocialMediaConnectionService,
)


class _FakeRepository:
    """In-memory stand-in for SocialMediaConnectionRepository, replicating
    the real repository's get_all-based implementation of
    list_by_business_profile/get_by_business_profile_and_platform."""

    def __init__(self) -> None:
        self.store: dict[uuid.UUID, SocialMediaConnection] = {}
        self.raise_on_write: Exception | None = None
        self.deleted: list[uuid.UUID] = []

    async def create(self, connection: SocialMediaConnection) -> SocialMediaConnection:
        if self.raise_on_write:
            raise self.raise_on_write
        connection.id = connection.id or uuid.uuid4()
        self.store[connection.id] = connection
        return connection

    async def get_by_id(self, connection_id: uuid.UUID) -> SocialMediaConnection | None:
        return self.store.get(connection_id)

    async def update(
        self, connection: SocialMediaConnection, data: dict
    ) -> SocialMediaConnection:
        if self.raise_on_write:
            raise self.raise_on_write
        for field, value in data.items():
            setattr(connection, field, value)
        return connection

    async def delete(self, connection: SocialMediaConnection) -> None:
        self.deleted.append(connection.id)
        self.store.pop(connection.id, None)

    async def get_all(
        self, *, filters: dict | None = None, limit: int = 20, offset: int = 0
    ):
        items = list(self.store.values())
        for field, value in (filters or {}).items():
            items = [c for c in items if getattr(c, field) == value]
        return items[offset : offset + limit], len(items)

    async def list_by_business_profile(
        self,
        business_profile_id,
        *,
        platform=None,
        connection_status=None,
        limit=20,
        offset=0,
    ):
        filters: dict[str, object] = {"business_profile_id": business_profile_id}
        if platform is not None:
            filters["platform"] = platform
        if connection_status is not None:
            filters["connection_status"] = connection_status
        return await self.get_all(filters=filters, limit=limit, offset=offset)

    async def get_by_business_profile_and_platform(self, business_profile_id, platform):
        items, _total = await self.get_all(
            filters={"business_profile_id": business_profile_id, "platform": platform},
            limit=1,
        )
        return items[0] if items else None


def _integrity_error(message: str) -> IntegrityError:
    return IntegrityError("STATEMENT", {}, Exception(message))


def _make_service():
    repo = _FakeRepository()
    session = AsyncMock()
    return SocialMediaConnectionService(session, repository=repo), repo, session


def _connect_payload(**overrides) -> SocialMediaConnectionCreate:
    data = {
        "business_profile_id": uuid.uuid4(),
        "platform": SocialMediaPlatform.INSTAGRAM,
        "access_token": "raw-access-token",
    }
    data.update(overrides)
    return SocialMediaConnectionCreate(**data)


async def test_connect_creates_new_connection_and_commits():
    service, repo, session = _make_service()

    result = await service.connect(_connect_payload())

    assert result.id in repo.store
    assert result.connection_status == SocialConnectionStatus.CONNECTED
    assert result.access_token == "raw-access-token"
    session.commit.assert_awaited_once()


async def test_connect_translates_invalid_business_profile_reference():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error(
        'insert or update on table "social_media_connections" violates foreign '
        'key constraint "social_media_connections_business_profile_id_fkey"'
    )

    with pytest.raises(InvalidReferenceError):
        await service.connect(_connect_payload())


async def test_connect_reraises_unrecognized_integrity_error():
    service, repo, _session = _make_service()
    repo.raise_on_write = _integrity_error("some_other_constraint_violation")

    with pytest.raises(IntegrityError):
        await service.connect(_connect_payload())


async def test_connect_reconnects_existing_platform_in_place_instead_of_duplicating():
    service, repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    first = await service.connect(
        _connect_payload(
            business_profile_id=business_profile_id, access_token="first-token"
        )
    )

    second = await service.connect(
        _connect_payload(
            business_profile_id=business_profile_id, access_token="second-token"
        )
    )

    assert second.id == first.id
    assert len(repo.store) == 1
    assert second.access_token == "second-token"


async def test_connect_reconnect_resets_status_from_disconnected_to_connected():
    service, repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    created = await service.connect(
        _connect_payload(business_profile_id=business_profile_id)
    )
    await service.disconnect(created.id)
    assert (
        repo.store[created.id].connection_status == SocialConnectionStatus.DISCONNECTED
    )

    reconnected = await service.connect(
        _connect_payload(
            business_profile_id=business_profile_id, access_token="fresh-token"
        )
    )

    assert reconnected.id == created.id
    assert reconnected.connection_status == SocialConnectionStatus.CONNECTED
    assert reconnected.access_token == "fresh-token"


async def test_get_missing_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(SocialMediaConnectionNotFoundError):
        await service.get(uuid.uuid4())


async def test_get_existing_returns_connection():
    service, _repo, _session = _make_service()
    created = await service.connect(_connect_payload())

    fetched = await service.get(created.id)

    assert fetched is created


async def test_list_filters_by_business_profile():
    service, _repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    other_business_profile_id = uuid.uuid4()
    await service.connect(_connect_payload(business_profile_id=business_profile_id))
    await service.connect(
        _connect_payload(
            business_profile_id=other_business_profile_id,
            platform=SocialMediaPlatform.LINKEDIN,
        )
    )

    items, total = await service.list(business_profile_id)

    assert total == 1
    assert items[0].business_profile_id == business_profile_id


async def test_list_filters_by_platform():
    service, _repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    await service.connect(
        _connect_payload(
            business_profile_id=business_profile_id,
            platform=SocialMediaPlatform.INSTAGRAM,
        )
    )
    await service.connect(
        _connect_payload(
            business_profile_id=business_profile_id,
            platform=SocialMediaPlatform.PINTEREST,
        )
    )

    items, total = await service.list(
        business_profile_id, platform=SocialMediaPlatform.PINTEREST
    )

    assert total == 1
    assert items[0].platform == SocialMediaPlatform.PINTEREST


async def test_list_filters_by_connection_status():
    service, _repo, _session = _make_service()
    business_profile_id = uuid.uuid4()
    connected = await service.connect(
        _connect_payload(
            business_profile_id=business_profile_id,
            platform=SocialMediaPlatform.INSTAGRAM,
        )
    )
    disconnected = await service.connect(
        _connect_payload(
            business_profile_id=business_profile_id,
            platform=SocialMediaPlatform.FACEBOOK,
        )
    )
    await service.disconnect(disconnected.id)

    items, total = await service.list(
        business_profile_id, connection_status=SocialConnectionStatus.CONNECTED
    )

    assert total == 1
    assert items[0].id == connected.id


async def test_disconnect_clears_tokens_and_sets_status():
    service, _repo, session = _make_service()
    created = await service.connect(_connect_payload())

    result = await service.disconnect(created.id)

    assert result.connection_status == SocialConnectionStatus.DISCONNECTED
    assert result.access_token is None
    assert result.refresh_token is None
    assert result.token_expiry is None
    session.commit.assert_awaited()


async def test_disconnect_missing_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(SocialMediaConnectionNotFoundError):
        await service.disconnect(uuid.uuid4())


async def test_refresh_token_updates_tokens_and_marks_connected():
    service, _repo, session = _make_service()
    created = await service.connect(_connect_payload())
    await service.disconnect(created.id)

    result = await service.refresh_token(
        created.id, RefreshTokenRequest(access_token="new-access-token")
    )

    assert result.access_token == "new-access-token"
    assert result.connection_status == SocialConnectionStatus.CONNECTED
    session.commit.assert_awaited()


async def test_refresh_token_missing_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(SocialMediaConnectionNotFoundError):
        await service.refresh_token(uuid.uuid4(), RefreshTokenRequest(access_token="x"))


async def test_sync_metadata_updates_only_provided_fields_and_stamps_last_sync():
    service, _repo, session = _make_service()
    created = await service.connect(_connect_payload(account_name="Old Name"))
    assert created.last_sync is None

    result = await service.sync_metadata(
        created.id, SyncMetadataRequest(account_name="New Name")
    )

    assert result.account_name == "New Name"
    assert result.account_id == created.account_id  # untouched
    assert result.last_sync is not None
    session.commit.assert_awaited()


async def test_sync_metadata_missing_raises_not_found():
    service, _repo, _session = _make_service()

    with pytest.raises(SocialMediaConnectionNotFoundError):
        await service.sync_metadata(uuid.uuid4(), SyncMetadataRequest())
