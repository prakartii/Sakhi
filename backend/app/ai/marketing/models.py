"""Pydantic schemas for Marketing Studio: analyzing content that's already
been posted (ContentAnalysis) and generating a brief for a future one
(ReelBrief). Both are LLM output shapes — see analyzer.py for how each is
produced and prompts.py for what the model is told to fill in.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContentMetrics(BaseModel):
    """Caller-supplied engagement numbers — never computed or guessed by
    the model; engagement_rate is the one derived value, computed in code
    (see analyzer.py._engagement_rate), not asked of the LLM."""

    views: int | None = Field(default=None, ge=0)
    likes: int | None = Field(default=None, ge=0)
    comments: int | None = Field(default=None, ge=0)
    shares: int | None = Field(default=None, ge=0)
    saves: int | None = Field(default=None, ge=0)


class RatedFeedback(BaseModel):
    rating: str = Field(..., description="A short verdict, e.g. 'Strong', 'Weak', 'Average'.")
    feedback: str


class AudienceSentiment(BaseModel):
    positive_pct: float = Field(..., ge=0, le=100)
    neutral_pct: float = Field(..., ge=0, le=100)
    negative_pct: float = Field(..., ge=0, le=100)
    summary: str


class ContentAnalysis(BaseModel):
    virality_score: float = Field(..., ge=0, le=100)
    virality_reasoning: str
    product_detection: list[str] = Field(default_factory=list)
    comment_themes: list[str] = Field(default_factory=list)
    comment_summary: str
    audience_sentiment: AudienceSentiment
    hook_analysis: RatedFeedback
    cta_analysis: RatedFeedback
    caption_analysis: RatedFeedback
    thumbnail_analysis: RatedFeedback | None = None
    recommendations: list[str] = Field(default_factory=list)
    ai_captions: list[str] = Field(default_factory=list)
    next_reel_ideas: list[str] = Field(default_factory=list)
    performance_summary: str


class ReelBrief(BaseModel):
    concept: str
    hook: str
    script_beats: list[str] = Field(default_factory=list)
    shot_list: list[str] = Field(default_factory=list)
    caption: str
    hashtags: list[str] = Field(default_factory=list)
    cta: str
    image_url: str | None = Field(
        default=None,
        description="A generated cover visual for this reel (Nano Banana), added after the "
        "brief itself — never populated by generate_reel_brief() directly.",
    )
    video_url: str | None = Field(
        default=None,
        description="A generated video for this reel (fal.ai) — a real, billed generation, "
        "added after the brief itself, never populated by generate_reel_brief() directly.",
    )
