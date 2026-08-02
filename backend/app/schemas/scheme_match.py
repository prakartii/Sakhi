"""Pydantic v2 response schemas for GET /schemes/matches.

Read-only and computed-on-read (see app/api/v1/endpoints/schemes.py):
match_score/is_eligible come from app.ai.rules.evaluate_criteria, why/basis
from app.ai.explanations — nothing here is written back to scheme_matches,
which stays reserved for a future "save/apply" tracking feature.
"""

from uuid import UUID

from pydantic import BaseModel

from app.models.enums import SchemeLevel


class SchemeMatchOut(BaseModel):
    scheme_id: UUID
    scheme_name: str
    scheme_code: str | None
    description: str | None
    issuing_authority: str | None
    scheme_level: SchemeLevel
    benefits: str | None
    application_url: str | None
    category: str | None
    match_score: float
    is_eligible: bool
    why: str
    basis: str


class SchemeMatchListResponse(BaseModel):
    items: list[SchemeMatchOut]
    total: int
