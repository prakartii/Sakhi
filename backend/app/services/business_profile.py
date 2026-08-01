"""Business logic for the Business Profile module.

Owns the transaction boundary (commit/rollback) around each use case and
translates database-level failures — a missing row, a constraint violation
— into domain exceptions the API layer maps to HTTP status codes. Routers
never see SQLAlchemy exceptions directly. Repositories only ever do
data access; any rule that requires interpreting what a value or a
constraint *means* — including what "onboarding complete" means — lives
here, not there.
"""

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business_profile import BusinessProfile
from app.models.enums import BusinessStatus
from app.repositories.business_profile import BusinessProfileRepository
from app.schemas.business_profile import (
    BusinessProfileCreate,
    BusinessProfileOnboardingStatus,
    BusinessProfilePut,
    BusinessProfileUpdate,
)

# Fields required for a profile to count as "onboarded." Deliberately a
# service-layer decision, not a schema or DB constraint: logo_url and the
# social links are useful but optional, so they're excluded on purpose —
# a business without an Instagram page isn't an incomplete profile.
_ONBOARDING_REQUIRED_FIELDS: tuple[str, ...] = (
    "business_name",
    "owner_name",
    "business_category",
    "business_description",
    "target_audience",
    "products_or_services",
    "business_stage",
    "city",
    "state",
    "country",
)


class BusinessProfileNotFoundError(Exception):
    """No business_profiles row exists for the given id."""


class BusinessProfileConflictError(Exception):
    """The write violates a uniqueness rule, e.g. two primary businesses
    for the same user (uq_business_profiles_primary_per_user)."""


class InvalidReferenceError(Exception):
    """A referenced user_id or preferred_language_id does not exist."""


def _translate_integrity_error(exc: IntegrityError) -> Exception:
    message = str(exc.orig).lower()
    if "uq_business_profiles_primary_per_user" in message:
        return BusinessProfileConflictError(
            "This user already has a primary business profile. "
            "Unset it (is_primary=false) before making another one primary."
        )
    if "business_profiles_user_id_fkey" in message:
        return InvalidReferenceError("user_id does not reference an existing user.")
    if "business_profiles_preferred_language_id_fkey" in message:
        return InvalidReferenceError(
            "preferred_language_id does not reference an existing language."
        )
    # Unrecognized constraint — surface as-is rather than mislabeling it;
    # the router lets this propagate as an unhandled 500.
    return exc


class BusinessProfileService:
    def __init__(
        self,
        session: AsyncSession,
        repository: BusinessProfileRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repository or BusinessProfileRepository(session)

    async def create(self, payload: BusinessProfileCreate) -> BusinessProfile:
        business_profile = BusinessProfile(**payload.model_dump())
        try:
            await self._repo.create(business_profile)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return business_profile

    async def get(self, business_profile_id: uuid.UUID) -> BusinessProfile:
        business_profile = await self._repo.get_by_id(business_profile_id)
        if business_profile is None:
            raise BusinessProfileNotFoundError(str(business_profile_id))
        return business_profile

    async def list(
        self,
        user_id: uuid.UUID,
        *,
        status: BusinessStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BusinessProfile], int]:
        return await self._repo.list_by_user(
            user_id, status=status, limit=limit, offset=offset
        )

    async def update(
        self, business_profile_id: uuid.UUID, payload: BusinessProfileUpdate
    ) -> BusinessProfile:
        """PATCH: applies only the fields the caller actually supplied."""
        business_profile = await self.get(business_profile_id)
        data = payload.model_dump(exclude_unset=True)
        try:
            await self._repo.update(business_profile, data)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return business_profile

    async def replace(
        self, business_profile_id: uuid.UUID, payload: BusinessProfilePut
    ) -> BusinessProfile:
        """PUT: applies the full payload — any field the caller omitted is
        reset to its schema default (see BusinessProfilePut), not left as
        whatever it was before. That's the difference from update()/PATCH."""
        business_profile = await self.get(business_profile_id)
        data = payload.model_dump()
        try:
            await self._repo.update(business_profile, data)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise _translate_integrity_error(exc) from exc
        return business_profile

    async def delete(self, business_profile_id: uuid.UUID) -> None:
        """Archives rather than hard-deletes: business_profiles is the
        parent of nearly every other table in the schema (memory,
        transactions, inventory, ...), so a real DELETE would cascade away
        a business's entire history. Setting status='archived' matches
        what the schema's status enum already exists for.
        """
        business_profile = await self.get(business_profile_id)
        await self._repo.archive(business_profile)
        await self._session.commit()

    async def get_onboarding_status(
        self, business_profile_id: uuid.UUID
    ) -> BusinessProfileOnboardingStatus:
        """Reports which of _ONBOARDING_REQUIRED_FIELDS are filled in.
        Pure read — computed from the row already fetched, no write."""
        business_profile = await self.get(business_profile_id)

        completed = [
            field
            for field in _ONBOARDING_REQUIRED_FIELDS
            if getattr(business_profile, field) not in (None, "")
        ]
        missing = [
            field for field in _ONBOARDING_REQUIRED_FIELDS if field not in completed
        ]

        return BusinessProfileOnboardingStatus(
            business_profile_id=business_profile.id,
            is_complete=not missing,
            completion_percentage=round(
                len(completed) / len(_ONBOARDING_REQUIRED_FIELDS) * 100, 2
            ),
            completed_fields=completed,
            missing_fields=missing,
        )
