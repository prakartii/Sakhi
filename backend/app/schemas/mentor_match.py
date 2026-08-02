"""Pydantic v2 response schemas for GET /mentors/matches.

Same compute-on-read pattern as app/schemas/scheme_match.py: match_score/
is_eligible from app.ai.rules.evaluate_criteria, why/basis from
app.ai.explanations, nothing persisted to mentor_matches.
"""

from uuid import UUID

from pydantic import BaseModel

from app.models.enums import MentorAvailability


class MentorMatchOut(BaseModel):
    mentor_id: UUID
    full_name: str
    bio: str | None
    expertise_areas: list[str]
    industry_focus: str | None
    years_experience: int | None
    avatar_url: str | None
    availability_status: MentorAvailability
    match_score: float
    is_eligible: bool
    why: str
    basis: str


class MentorMatchListResponse(BaseModel):
    items: list[MentorMatchOut]
    total: int
