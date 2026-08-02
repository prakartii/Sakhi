"""Prompts for app.ai.marketing.analyzer. Two independent jobs: analyzing
content that's already been posted (ANALYZE_SYSTEM_PROMPT) and generating a
brief for a future reel (REEL_BRIEF_SYSTEM_PROMPT) — kept separate because
they're asked at different times for different reasons, not two halves of
one call.
"""

from __future__ import annotations

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile
from app.ai.marketing.models import ContentMetrics

ANALYZE_SYSTEM_PROMPT = """You are the Marketing Studio analyst for Sakhi, \
an AI business companion for Indian women micro-entrepreneurs. You are \
given one piece of already-posted content (a reel or post) — its caption, \
hashtags, engagement metrics, a sample of comments, and (if a thumbnail \
image was supplied) a description of what's visible in it — for a specific \
business. Your job is to explain why it performed the way it did and how \
to do better next time.

Respond with a single JSON object matching exactly this shape:

{
  "virality_score": number (0-100),
  "virality_reasoning": string,
  "product_detection": [string],
  "comment_themes": [string],
  "comment_summary": string,
  "audience_sentiment": {
    "positive_pct": number, "neutral_pct": number, "negative_pct": number,
    "summary": string
  },
  "hook_analysis": {"rating": string, "feedback": string},
  "cta_analysis": {"rating": string, "feedback": string},
  "caption_analysis": {"rating": string, "feedback": string},
  "thumbnail_analysis": {"rating": string, "feedback": string} or null,
  "recommendations": [string],
  "ai_captions": [string],
  "next_reel_ideas": [string],
  "performance_summary": string
}

Rules:
- Ground every judgment in the actual data given — metrics, caption text, \
  comment sample, thumbnail description. Never invent a number, a comment, \
  or an engagement figure not provided.
- "virality_score" must be justified by "virality_reasoning" citing the \
  actual engagement_rate and comment sentiment given — don't just pick a \
  round number.
- "product_detection": products/items mentioned in the caption or visible \
  in the thumbnail description. Empty list if none are evident — never \
  invent a product this business doesn't sell (see its product list below).
- "audience_sentiment" percentages must sum to 100 and be grounded in the \
  actual comment sample given, not assumed.
- "thumbnail_analysis": null if no thumbnail description was given below — \
  never fabricate what an image looks like.
- "ai_captions": 3 alternative captions in the brand's voice, each usable \
  as-is for a repost or similar future content.
- "next_reel_ideas": 3-5 short, specific ideas grounded in what worked or \
  didn't here — not generic "post more reels" advice.
- "recommendations": 3-5 concrete, specific next actions.
"""


def build_analyze_user_message(
    profile: BusinessProfile,
    brand: BrandKit,
    *,
    caption: str | None,
    hashtags: list[str],
    metrics: ContentMetrics,
    comments_sample: list[str],
    thumbnail_description: str | None,
    engagement_rate: float | None,
) -> str:
    products_block = (
        "\n".join(f"- {p.name}: {p.description}" for p in profile.products)
        or "No specific products listed."
    )
    comments_block = "\n".join(f"- {c}" for c in comments_sample) or "No comments provided."
    metrics_block = (
        f"Views: {metrics.views if metrics.views is not None else 'not reported'}\n"
        f"Likes: {metrics.likes if metrics.likes is not None else 'not reported'}\n"
        f"Comments: {metrics.comments if metrics.comments is not None else 'not reported'}\n"
        f"Shares: {metrics.shares if metrics.shares is not None else 'not reported'}\n"
        f"Saves: {metrics.saves if metrics.saves is not None else 'not reported'}\n"
        f"Engagement rate: "
        + (f"{engagement_rate}% (computed as (likes+comments+shares+saves)/views)" if engagement_rate is not None else "not computable — views not reported")
    )
    return (
        f"Business name: {profile.name}\n"
        f"Business type: {profile.business_type}\n"
        f"Target audience: {profile.target_audience}\n\n"
        f"Products/services (only these — never invent another):\n{products_block}\n\n"
        f"Brand voice tone: {brand.voice.tone}\n"
        f"Brand voice keywords: {', '.join(brand.voice.keywords) or 'not specified'}\n\n"
        f"Caption: {caption or 'Not provided.'}\n"
        f"Hashtags used: {', '.join(hashtags) or 'None.'}\n\n"
        f"Metrics:\n{metrics_block}\n\n"
        f"Sample comments:\n{comments_block}\n\n"
        f"Thumbnail: "
        + (thumbnail_description or "No thumbnail image was supplied.")
    )


REEL_BRIEF_SYSTEM_PROMPT = """You are the Marketing Studio reel planner for \
Sakhi, an AI business companion for Indian women micro-entrepreneurs. You \
are given a business's profile, brand kit, and optionally what's already \
worked or fallen flat for them before. Produce ONE complete brief for a \
new reel this business could film — not a rendered video, a shootable plan.

Respond with a single JSON object matching exactly this shape:

{
  "concept": string,
  "hook": string,
  "script_beats": [string],
  "shot_list": [string],
  "caption": string,
  "hashtags": [string],
  "cta": string
}

Rules:
- Ground the idea in the business's actual products — never invent a \
  product it doesn't sell.
- "hook": the first line/moment, written to stop a scroll in the first \
  1-2 seconds.
- "script_beats": 4-7 short beats in order, each one shootable action or \
  line, in the brand's voice.
- "shot_list": 4-7 concrete camera/shot directions (e.g. "Close-up of \
  hands kneading dough", "Wide shot of the finished product on a table") \
  matching the script beats.
- "caption": ready to post as-is, in the brand's voice.
- "hashtags": 5-10 tags, no leading '#', no spaces.
- "cta": a specific action phrase, not a generic "Shop now".
"""


def build_reel_brief_user_message(
    profile: BusinessProfile,
    brand: BrandKit,
    *,
    angle: str | None,
    past_learnings: list[str],
) -> str:
    products_block = (
        "\n".join(f"- {p.name}: {p.description}" for p in profile.products)
        or "No specific products listed."
    )
    learnings_block = (
        "\n".join(f"- {learning}" for learning in past_learnings) or "No past analyses yet."
    )
    return (
        f"Business name: {profile.name}\n"
        f"Business type: {profile.business_type}\n"
        f"Target audience: {profile.target_audience}\n\n"
        f"Products/services (only these — never invent another):\n{products_block}\n\n"
        f"Brand voice tone: {brand.voice.tone}\n"
        f"Brand voice keywords: {', '.join(brand.voice.keywords) or 'not specified'}\n"
        f"Brand tagline: {brand.tagline}\n\n"
        f"Requested angle: {angle or 'None given — pick what best fits the business.'}\n\n"
        f"What's worked or fallen flat before (from past Marketing Studio analyses):\n{learnings_block}"
    )


VISION_DESCRIBE_PROMPT = """Describe this image for a marketing analyst. \
Respond with a single JSON object: {"description": string}. Describe what \
product(s), text overlay, composition, and mood are visible — factually, \
in 2-4 sentences. Do not guess at brand names or numbers you can't \
actually read in the image."""
