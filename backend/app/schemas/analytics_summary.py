"""Response schema for GET /business-profiles/{id}/ai-summary."""

from pydantic import BaseModel


class TopActionOut(BaseModel):
    action: str
    why: str


class AISummaryResponse(BaseModel):
    narrative: str
    highlights: list[str]
    top_actions: list[TopActionOut]
