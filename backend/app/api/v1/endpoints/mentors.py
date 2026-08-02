"""Mentor-matching endpoint: ranks the mentor_profiles directory against
one business's own profile facts.

Same compute-on-read pattern as app/api/v1/endpoints/schemes.py — nothing
persisted to mentor_matches. Deliberately has no seed data: fabricating
fictitious real-seeming mentor people would be worse than an honest empty
directory, so this returns whatever mentor_profiles rows actually exist
(none yet, in a fresh environment) and the frontend renders a graceful
"no mentors yet" empty state rather than assuming there's always at least
one match.

No authentication yet: business_profile_id is a required query param, same
deliberate temporary gap as every other endpoint module in this project.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.explanations import ExplanationRequest, explain
from app.ai.providers.base import AIProviderError
from app.ai.rules import Criterion, MatchResult, evaluate_criteria, to_explanation_facts
from app.api.deps import get_business_profile_repository, get_mentor_repository
from app.models.business_profile import BusinessProfile
from app.models.mentor_profile import MentorProfile
from app.repositories.business_profile import BusinessProfileRepository
from app.repositories.mentor import MentorRepository
from app.schemas.mentor_match import MentorMatchListResponse, MentorMatchOut

router = APIRouter()

_DEFAULT_TOP_N = 5
_DIRECTORY_LIMIT = 100


@router.get(
    "/matches",
    response_model=MentorMatchListResponse,
    summary="Active mentors ranked against a business's own profile (app.ai.rules + app.ai.explanations)",
    responses={404: {"description": "Business profile not found"}},
)
async def list_mentor_matches(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    top_n: int = Query(_DEFAULT_TOP_N, ge=1, le=20),
    profile_repo: BusinessProfileRepository = Depends(get_business_profile_repository),
    mentor_repo: MentorRepository = Depends(get_mentor_repository),
) -> MentorMatchListResponse:
    """Scores every active mentor's fit for this business — available and
    expertise-matched first — highest match_score first. Returns an empty
    list, not a 404 or error, when the mentor directory has no rows yet."""
    profile = await profile_repo.get_by_id(business_profile_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business profile not found.")

    mentors, _ = await mentor_repo.list_active(limit=_DIRECTORY_LIMIT)

    scored = [
        (mentor, evaluate_criteria(_mentor_facts(mentor), _fit_criteria(profile)))
        for mentor in mentors
    ]
    scored.sort(key=lambda pair: pair[1].match_score, reverse=True)

    items: list[MentorMatchOut] = []
    for mentor, result in scored[:top_n]:
        why, basis = await _narrate(mentor.full_name, result)
        items.append(
            MentorMatchOut(
                mentor_id=mentor.id,
                full_name=mentor.full_name,
                bio=mentor.bio,
                expertise_areas=mentor.expertise_areas,
                industry_focus=mentor.industry_focus,
                years_experience=mentor.years_experience,
                avatar_url=mentor.avatar_url,
                availability_status=mentor.availability_status,
                match_score=result.match_score,
                is_eligible=result.is_eligible,
                why=why,
                basis=basis,
            )
        )
    return MentorMatchListResponse(items=items, total=len(items))


def _mentor_facts(mentor: MentorProfile) -> dict[str, object]:
    """Deterministic facts about one mentor — no LLM."""
    return {
        "mentor_availability": mentor.availability_status.value,
        "mentor_expertise": mentor.expertise_areas,
    }


def _fit_criteria(profile: BusinessProfile) -> list[Criterion]:
    """What a good mentor match looks like for this business: available
    now (required), plus expertise overlapping the business's own
    industry/category (soft — an unavailable-but-relevant mentor should
    still surface, just lower and marked not-yet-eligible)."""
    interests = [v for v in (profile.industry, profile.business_category) if v]
    criteria = [
        Criterion(
            field="mentor_availability",
            operator="eq",
            value="available",
            required=True,
            label="Mentor is currently available",
        ),
    ]
    if interests:
        criteria.append(
            Criterion(
                field="mentor_expertise",
                operator="overlaps",
                value=interests,
                weight=2,
                required=False,
                label="Mentor's expertise matches your industry",
            )
        )
    return criteria


async def _narrate(mentor_name: str, result: MatchResult) -> tuple[str, str]:
    facts = to_explanation_facts(result)
    try:
        explanation = await explain(
            ExplanationRequest(
                subject=f"{result.match_score:.0f}% match with {mentor_name}", facts=facts
            )
        )
        return explanation.why, explanation.basis
    except AIProviderError:
        why = f"Estimated {result.match_score:.0f}% match based on your business profile."
        basis = "; ".join(facts) if facts else "No fit criteria configured."
        return why, basis
