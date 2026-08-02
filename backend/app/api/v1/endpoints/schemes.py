"""Scheme-matching endpoint: ranks the government_schemes catalog against
one business's own profile facts.

Computed on read, not persisted — scheme_matches stays reserved for a
future "save/apply" tracking feature (same choice app.services.inventory's
forecast and app.ai.analytics.summarize make: deterministic computation
first, narration second, nothing written back). The rules engine
(app.ai.rules.evaluate_criteria, no LLM) decides match_score/is_eligible;
app.ai.explanations turns that into the why/basis prose shown on the card.

No authentication yet: business_profile_id is a required query param, same
deliberate temporary gap as every other endpoint module in this project.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.explanations import ExplanationRequest, explain
from app.ai.providers.base import AIProviderError
from app.ai.rules import Criterion, MatchResult, evaluate_criteria, to_explanation_facts
from app.api.deps import get_business_profile_repository, get_government_scheme_repository
from app.models.business_profile import BusinessProfile
from app.models.government_scheme import GovernmentScheme
from app.repositories.business_profile import BusinessProfileRepository
from app.repositories.government_scheme import GovernmentSchemeRepository
from app.schemas.scheme_match import SchemeMatchListResponse, SchemeMatchOut

router = APIRouter()

_DEFAULT_TOP_N = 5
_CATALOG_LIMIT = 100


@router.get(
    "/matches",
    response_model=SchemeMatchListResponse,
    summary="Government schemes ranked against a business's own profile (app.ai.rules + app.ai.explanations)",
    responses={404: {"description": "Business profile not found"}},
)
async def list_scheme_matches(
    business_profile_id: uuid.UUID = Query(..., description="Owning business id."),
    top_n: int = Query(_DEFAULT_TOP_N, ge=1, le=20),
    profile_repo: BusinessProfileRepository = Depends(get_business_profile_repository),
    scheme_repo: GovernmentSchemeRepository = Depends(get_government_scheme_repository),
) -> SchemeMatchListResponse:
    """Scores every active scheme's eligibility_criteria against this
    business's own facts, highest match_score first. Schemes the business
    doesn't (yet) qualify for are still returned — is_eligible=False,
    lower score — so a near-miss can still be surfaced with the reason,
    same UX as the original Stand-Up India 61% mock."""
    profile = await profile_repo.get_by_id(business_profile_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Business profile not found.")

    facts = _build_business_facts(profile)
    schemes, _ = await scheme_repo.list_active(limit=_CATALOG_LIMIT)

    scored = [(scheme, evaluate_criteria(facts, _scheme_criteria(scheme))) for scheme in schemes]
    scored.sort(key=lambda pair: pair[1].match_score, reverse=True)

    items: list[SchemeMatchOut] = []
    for scheme, result in scored[:top_n]:
        why, basis = await _narrate(scheme.scheme_name, result)
        items.append(
            SchemeMatchOut(
                scheme_id=scheme.id,
                scheme_name=scheme.scheme_name,
                scheme_code=scheme.scheme_code,
                description=scheme.description,
                issuing_authority=scheme.issuing_authority,
                scheme_level=scheme.scheme_level,
                benefits=scheme.benefits,
                application_url=scheme.application_url,
                category=scheme.category,
                match_score=result.match_score,
                is_eligible=result.is_eligible,
                why=why,
                basis=basis,
            )
        )
    return SchemeMatchListResponse(items=items, total=len(items))


def _build_business_facts(profile: BusinessProfile) -> dict[str, object]:
    """Deterministic facts derivable from a business_profiles row — no LLM.
    Only fields that actually exist on the model are used; there is no
    gender field to check (Sakhi's user base is women entrepreneurs by
    construction), so "women-led" is never one of these facts."""
    facts: dict[str, object] = {
        "registration_type": profile.registration_type.value,
        "has_udyam_registration": bool(profile.udyam_registration_number),
        "state": profile.state,
    }
    if profile.year_established:
        facts["business_age_months"] = max(
            0, (date.today().year - profile.year_established) * 12
        )
    return facts


def _scheme_criteria(scheme: GovernmentScheme) -> list[Criterion]:
    """Combines a scheme's free-form eligibility_criteria (JSONB, authored
    per-scheme in the seed migration) with Criterion objects derived from
    its own typed columns (min_business_age_months, applicable_states),
    so those columns don't have to be duplicated into every scheme's JSON."""
    criteria = [Criterion(**c) for c in scheme.eligibility_criteria.get("criteria", [])]
    if scheme.min_business_age_months:
        criteria.append(
            Criterion(
                field="business_age_months",
                operator="gte",
                value=scheme.min_business_age_months,
                required=True,
                label=f"Business is at least {scheme.min_business_age_months} months old",
            )
        )
    if scheme.applicable_states:
        criteria.append(
            Criterion(
                field="state",
                operator="in",
                value=scheme.applicable_states,
                required=True,
                label="Business is located in an eligible state",
            )
        )
    return criteria


async def _narrate(scheme_name: str, result: MatchResult) -> tuple[str, str]:
    facts = to_explanation_facts(result)
    try:
        explanation = await explain(
            ExplanationRequest(
                subject=f"{result.match_score:.0f}% match with {scheme_name}", facts=facts
            )
        )
        return explanation.why, explanation.basis
    except AIProviderError:
        # Graceful degrade: a score-only fallback rather than failing the
        # whole ranked list because one narration call errored.
        why = f"Estimated {result.match_score:.0f}% match based on your business profile."
        basis = "; ".join(facts) if facts else "No eligibility criteria configured for this scheme."
        return why, basis
