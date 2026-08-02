"""Business logic for Website Management.

Owns the transaction boundary (commit/rollback) around each use case and
translates database-level failures into domain exceptions the API layer
maps to HTTP status codes — routers never see SQLAlchemy exceptions
directly. Format/shape validation (domain shape, URL scheme, non-blank
website_name) lives in the Pydantic schemas at the API boundary, matching
Business Profile's and Brand Assets' established pattern.

The one genuinely interpretive rule that lives here, not in a schema or a
repository: "support version history" means every create/update/archive of
a website automatically produces an immutable website_versions snapshot,
numbered sequentially per website. There is no separate "author a version"
endpoint — versions are a side effect of writes, the same way a Git commit
is a side effect of `git commit`, not something requested independently.
"""

from __future__ import annotations
# ^ Load-bearing, not stylistic: this class has a method literally named
# `list`. Once that `def list(...)` binds in the class namespace, any
# LATER method (list_versions, get_version) that writes a bare `list[...]`
# in its own return annotation would otherwise resolve `list` to that
# method instead of the builtin, and blow up with "'function' object is
# not subscriptable" the moment the module is imported. Deferred/string
# annotations sidestep the whole class of bug. See app/repositories/base.py
# for the same technique used for a different reason.

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import WebsiteStatus
from app.models.website import Website
from app.models.website_version import WebsiteVersion
from app.repositories.website import WebsiteRepository
from app.repositories.website_version import WebsiteVersionRepository
from app.schemas.website import WebsiteCreate, WebsiteUpdate

# The Website columns snapshotted into every website_versions row. Kept as
# one explicit list so WebsiteVersion's shape and this service's snapshot
# logic can't silently drift apart from each other.
_SNAPSHOT_FIELDS = (
    "website_name",
    "deployment_url",
    "github_repository",
    "template",
    "status",
    "seo_title",
    "seo_description",
    "custom_domain",
    "favicon",
    "published",
    "content",
    "images",
)


class WebsiteNotFoundError(Exception):
    """No websites row exists for the given id."""


class WebsiteVersionNotFoundError(Exception):
    """No website_versions row exists for the given website/version_number."""


class WebsiteConflictError(Exception):
    """The write violates a uniqueness rule, e.g. custom_domain already
    used by another website (uq_websites_custom_domain)."""


class InvalidReferenceError(Exception):
    """The referenced business_profile_id does not exist."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "uq_websites_custom_domain" in message:
        return WebsiteConflictError(
            "custom_domain is already in use by another website."
        )
    if "websites_business_profile_id_fkey" in message:
        return InvalidReferenceError(
            "business_profile_id does not reference an existing business profile."
        )
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500.
    return exc


class WebsiteService:
    def __init__(
        self,
        session: AsyncSession,
        repository: WebsiteRepository | None = None,
        version_repository: WebsiteVersionRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or WebsiteRepository(session)
        self._version_repo = version_repository or WebsiteVersionRepository(session)

    async def create(self, payload: WebsiteCreate) -> Website:
        website = Website(**payload.model_dump())
        try:
            await self._repo.create(website)
            await self._record_version(website, change_notes="Initial version")
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return website

    async def get(self, website_id: uuid.UUID) -> Website:
        website = await self._repo.get_by_id(website_id)
        if website is None:
            raise WebsiteNotFoundError(str(website_id))
        return website

    async def list(
        self,
        business_profile_id: uuid.UUID,
        *,
        status: WebsiteStatus | None = None,
        published: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Website], int]:
        return await self._repo.list_by_business_profile(
            business_profile_id,
            status=status,
            published=published,
            limit=limit,
            offset=offset,
        )

    async def update(self, website_id: uuid.UUID, payload: WebsiteUpdate) -> Website:
        """PATCH: applies only the fields the caller actually supplied, then
        records a new version snapshot of the resulting state.
        `change_notes` is carried through to that snapshot and is never
        applied to the website row itself — it isn't a website column.
        """
        website = await self.get(website_id)
        data = payload.model_dump(exclude_unset=True)
        change_notes = data.pop("change_notes", None)
        try:
            await self._repo.update(website, data)
            await self._record_version(website, change_notes=change_notes)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return website

    async def update_content(
        self,
        website_id: uuid.UUID,
        *,
        content: dict,
        images: dict | None = None,
        seo_title: str | None = None,
        seo_description: str | None = None,
        change_notes: str | None = None,
    ) -> Website:
        """Persist AI-generated/refined site content (+ optionally synced
        SEO metadata) as a single version snapshot — the counterpart to
        update() for writes that come from app.ai.website rather than a
        user-supplied WebsiteUpdate payload. `images` is only overwritten
        when explicitly given (a refinement turn that doesn't touch images
        shouldn't erase the existing ones). seo_title/seo_description are
        folded in here too — rather than a separate update() call — so one
        chat turn produces exactly one version, not two.
        """
        website = await self.get(website_id)
        website.content = content
        if images is not None:
            website.images = images
        if seo_title is not None:
            website.seo_title = seo_title
        if seo_description is not None:
            website.seo_description = seo_description
        await self._session.flush()
        await self._record_version(website, change_notes=change_notes)
        await self._session.commit()
        return website

    async def delete(self, website_id: uuid.UUID) -> None:
        """Archives rather than hard-deletes: a website can have real work
        invested in it (SEO copy, a paid custom domain, a deployment
        link), `status` already has an 'archived' value for exactly this,
        and there's no undo on a REST DELETE. Also records a version
        snapshot of the archived state, so the history shows exactly when
        — and from what state — it was retired.
        """
        website = await self.get(website_id)
        await self._repo.archive(website)
        await self._record_version(website, change_notes="Archived")
        await self._session.commit()

    async def list_versions(
        self, website_id: uuid.UUID, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[WebsiteVersion], int]:
        await self.get(website_id)  # 404s cleanly if the website itself is missing
        return await self._version_repo.list_by_website(
            website_id, limit=limit, offset=offset
        )

    async def get_version(
        self, website_id: uuid.UUID, version_number: int
    ) -> WebsiteVersion:
        await self.get(website_id)
        version = await self._version_repo.get_by_website_and_version(
            website_id, version_number
        )
        if version is None:
            raise WebsiteVersionNotFoundError(f"{website_id}/{version_number}")
        return version

    async def _record_version(
        self, website: Website, *, change_notes: str | None
    ) -> WebsiteVersion:
        # version_number is scoped per-website, not global, so it can't be a
        # simple DB sequence — the count-so-far is the next number. The
        # uq_website_versions_website_version constraint (not this count) is
        # what actually guards against a concurrent-write race.
        existing_count = await self._version_repo.count(
            filters={"website_id": website.id}
        )
        version = WebsiteVersion(
            website_id=website.id,
            version_number=existing_count + 1,
            change_notes=change_notes,
            **{field: getattr(website, field) for field in _SNAPSHOT_FIELDS},
        )
        await self._version_repo.create(version)
        return version
