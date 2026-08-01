"""Business logic for Scheduled Posts.

Owns the transaction boundary (commit/rollback) around each use case and
translates database-level failures into domain exceptions the API layer
maps to HTTP status codes — routers never see SQLAlchemy exceptions
directly. Format/shape validation lives in the Pydantic schemas at the API
boundary; the genuinely interpretive rules here — whether
content_calendar_id/social_connection_id actually belong to the same
business (and platform), whether a connection is actually connected, and
whether a status transition is allowed — all require reading other rows'
data, not just checking this payload's shape, so they live in this service.

No platform API calls and no publishing happen anywhere in this module.
Update Status exists to *record* what a future publishing worker reports
back, the same "record data obtained elsewhere" pattern already
established by RefreshTokenRequest/SyncMetadataRequest in the Social Media
Connections module — it does not call anything itself.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_calendar_item import ContentCalendarItem
from app.models.enums import (
    PublishingStatus,
    SocialConnectionStatus,
    SocialMediaPlatform,
)
from app.models.scheduled_post import ScheduledPost
from app.repositories.content_calendar_item import ContentCalendarItemRepository
from app.repositories.scheduled_post import ScheduledPostRepository
from app.repositories.social_media_connection import SocialMediaConnectionRepository
from app.schemas.scheduled_post import ScheduledPostCreate, UpdateStatusRequest

_TERMINAL_STATUSES = (PublishingStatus.PUBLISHED, PublishingStatus.CANCELLED)


class ScheduledPostNotFoundError(Exception):
    """No scheduled_posts row exists for the given id."""


class InvalidReferenceError(Exception):
    """The referenced business_profile_id does not exist."""


class InvalidContentCalendarReferenceError(Exception):
    """content_calendar_id doesn't exist or doesn't belong to the same
    business."""


class InvalidSocialConnectionError(Exception):
    """social_connection_id doesn't exist, doesn't belong to the same
    business, doesn't match the content item's platform, or isn't
    currently connected."""


class InvalidScheduleError(Exception):
    """scheduled_time is not in the future."""


class InvalidStatusTransitionError(Exception):
    """The requested status change isn't valid from the post's current
    publishing_status."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "scheduled_posts_business_profile_id_fkey" in message:
        return InvalidReferenceError(
            "business_profile_id does not reference an existing business profile."
        )
    if "scheduled_posts_content_calendar_id_fkey" in message:
        return InvalidContentCalendarReferenceError(
            "content_calendar_id does not reference an existing content "
            "calendar item."
        )
    if "scheduled_posts_social_connection_id_fkey" in message:
        return InvalidSocialConnectionError(
            "social_connection_id does not reference an existing social "
            "media connection."
        )
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500.
    return exc


class ScheduledPostService:
    def __init__(
        self,
        session: AsyncSession,
        repository: ScheduledPostRepository | None = None,
        content_calendar_repository: ContentCalendarItemRepository | None = None,
        connection_repository: SocialMediaConnectionRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or ScheduledPostRepository(session)
        self._content_repo = (
            content_calendar_repository or ContentCalendarItemRepository(session)
        )
        self._connection_repo = (
            connection_repository or SocialMediaConnectionRepository(session)
        )

    async def _validate_content_calendar_reference(
        self, business_profile_id: uuid.UUID, content_calendar_id: uuid.UUID
    ) -> ContentCalendarItem:
        item = await self._content_repo.get_by_id(content_calendar_id)
        if item is None:
            raise InvalidContentCalendarReferenceError(
                "content_calendar_id does not reference an existing content "
                "calendar item."
            )
        if item.business_profile_id != business_profile_id:
            raise InvalidContentCalendarReferenceError(
                "content_calendar_id does not belong to the same "
                "business_profile_id."
            )
        return item

    async def _validate_social_connection(
        self,
        business_profile_id: uuid.UUID,
        social_connection_id: uuid.UUID,
        platform: SocialMediaPlatform,
    ) -> None:
        connection = await self._connection_repo.get_by_id(social_connection_id)
        if connection is None:
            raise InvalidSocialConnectionError(
                "social_connection_id does not reference an existing social "
                "media connection."
            )
        if connection.business_profile_id != business_profile_id:
            raise InvalidSocialConnectionError(
                "social_connection_id does not belong to the same "
                "business_profile_id."
            )
        if connection.platform != platform:
            raise InvalidSocialConnectionError(
                "social_connection_id's platform does not match the content "
                "item's platform."
            )
        if connection.connection_status != SocialConnectionStatus.CONNECTED:
            raise InvalidSocialConnectionError(
                "social_connection_id is not currently connected."
            )

    async def schedule_post(self, payload: ScheduledPostCreate) -> ScheduledPost:
        if payload.scheduled_time <= datetime.now(timezone.utc):
            raise InvalidScheduleError("scheduled_time must be in the future.")
        content_item = await self._validate_content_calendar_reference(
            payload.business_profile_id, payload.content_calendar_id
        )
        await self._validate_social_connection(
            payload.business_profile_id,
            payload.social_connection_id,
            content_item.platform,
        )
        # publishing_status/retry_count are set explicitly rather than left
        # to their column server_defaults, so a freshly scheduled post is
        # correct immediately — same reasoning as NotificationService.create
        # setting is_read explicitly instead of depending on a flush/
        # RETURNING round trip to populate it.
        scheduled_post = ScheduledPost(
            **payload.model_dump(),
            publishing_status=PublishingStatus.QUEUED,
            retry_count=0,
        )
        try:
            await self._repo.create(scheduled_post)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return scheduled_post

    async def get(self, scheduled_post_id: uuid.UUID) -> ScheduledPost:
        scheduled_post = await self._repo.get_by_id(scheduled_post_id)
        if scheduled_post is None:
            raise ScheduledPostNotFoundError(str(scheduled_post_id))
        return scheduled_post

    async def get_queue(
        self,
        business_profile_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ScheduledPost], int]:
        return await self._repo.list_queue(
            business_profile_id, limit=limit, offset=offset
        )

    async def publishing_history(
        self,
        business_profile_id: uuid.UUID,
        *,
        publishing_status: PublishingStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ScheduledPost], int]:
        return await self._repo.list_history(
            business_profile_id,
            publishing_status=publishing_status,
            limit=limit,
            offset=offset,
        )

    async def cancel_schedule(self, scheduled_post_id: uuid.UUID) -> ScheduledPost:
        """Idempotent if already cancelled. Cannot cancel a post that has
        already published — there's nothing left to prevent."""
        scheduled_post = await self.get(scheduled_post_id)
        if scheduled_post.publishing_status == PublishingStatus.CANCELLED:
            return scheduled_post
        if scheduled_post.publishing_status == PublishingStatus.PUBLISHED:
            raise InvalidStatusTransitionError(
                "cannot cancel a post that has already been published."
            )
        await self._repo.update(
            scheduled_post, {"publishing_status": PublishingStatus.CANCELLED}
        )
        await self._session.commit()
        return scheduled_post

    async def retry_failed_post(self, scheduled_post_id: uuid.UUID) -> ScheduledPost:
        """Only a failed post can be retried — requeues it and increments
        retry_count. error_log is left as-is (the last failure reason
        stays visible until the next Update Status call reports a new
        outcome), and no cap on retry_count is enforced at this layer."""
        scheduled_post = await self.get(scheduled_post_id)
        if scheduled_post.publishing_status != PublishingStatus.FAILED:
            raise InvalidStatusTransitionError("only a failed post can be retried.")
        await self._repo.update(
            scheduled_post,
            {
                "publishing_status": PublishingStatus.QUEUED,
                "retry_count": scheduled_post.retry_count + 1,
            },
        )
        await self._session.commit()
        return scheduled_post

    async def update_status(
        self, scheduled_post_id: uuid.UUID, payload: UpdateStatusRequest
    ) -> ScheduledPost:
        """Records the outcome of a publish attempt made elsewhere. Not a
        partial patch: every call replaces published_url/provider_response/
        error_log with exactly what this report says (a fresh attempt's
        outcome, not a merge with the previous one). Cannot be called once
        a post is already published or cancelled — those are terminal;
        Cancel Schedule and Retry Failed Post are the only ways out of
        them.
        """
        scheduled_post = await self.get(scheduled_post_id)
        if scheduled_post.publishing_status in _TERMINAL_STATUSES:
            raise InvalidStatusTransitionError(
                f"cannot update status of a post that is already "
                f"{scheduled_post.publishing_status.value}."
            )
        data: dict[str, object] = {
            "publishing_status": payload.publishing_status,
            "published_url": payload.published_url,
            "provider_response": payload.provider_response,
            "error_log": payload.error_log,
        }
        if payload.publishing_status == PublishingStatus.PUBLISHED:
            data["published_at"] = datetime.now(timezone.utc)
        await self._repo.update(scheduled_post, data)
        await self._session.commit()
        return scheduled_post
