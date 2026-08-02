"""Prompt for generate_calendar() (see generator.py). The schedule itself
(dates/platforms/types/times) is already decided by scheduler.py before
this prompt is built — the model only writes copy for each given slot.
"""

from __future__ import annotations

from app.ai.brand.models import BrandKit
from app.ai.business.models import BusinessProfile
from app.ai.content.models import CampaignFocus, ScheduledSlot

# One line per campaign focus, appended to the user message so the whole
# month's copy leans into a single theme instead of generic day-to-day
# posting. "general" adds nothing — the default, unthemed behavior.
_CAMPAIGN_FOCUS_INSTRUCTIONS: dict[str, str] = {
    "festival": (
        "Campaign focus: FESTIVAL & SEASONAL. Lean into any festival noted "
        "against a slot, and where no festival is noted, write seasonal/"
        "occasion-led copy anyway (gifting, festive prep, seasonal use of "
        "the product) rather than a generic daily post."
    ),
    "product_launch": (
        "Campaign focus: PRODUCT LAUNCH. Build a launch arc across the "
        "slots — early posts building anticipation ('coming soon'), a "
        "clear launch-day announcement on an early slot, then follow-up "
        "posts reinforcing the new product. Center the launch note below."
    ),
    "promotional_offer": (
        "Campaign focus: PROMOTIONAL OFFER. Center the offer described "
        "below across the slots — building urgency (limited time/stock), "
        "a clear value statement, and a strong CTA to redeem it before it "
        "ends."
    ),
    "bundle_idea": (
        "Campaign focus: BUNDLE. Pitch the product bundle described below "
        "— why these products work together, the value of buying them as "
        "a set versus separately, and a CTA to buy the bundle."
    ),
}

SYSTEM_PROMPT = """You are the Content Calendar copywriter for Sakhi, an \
AI business companion for Indian women micro-entrepreneurs. You are given \
a business profile, its brand kit, and an already-decided schedule of \
post slots (date, platform, post type, and — for some dates — a festival \
it falls near). You do NOT choose dates, platforms, or post types — those \
are already decided. Your only job is to write the copy for each slot.

Respond with a single JSON object matching exactly this shape:

{
  "posts": [
    {
      "caption": string,
      "hashtags": [string],
      "reel_script": string or null,
      "carousel_slides": [string] or null,
      "image_prompt": string,
      "cta": string
    }
  ]
}

"posts" MUST have exactly as many entries as the slots listed below, in \
the exact same order — entry N is the copy for slot N.

Rules:
- Write in the brand's established voice (tone + keywords) — every \
  caption should sound like it came from the same brand.
- Ground every caption in the business's actual products; never invent a \
  product that isn't listed. For a slot with a festival noted, tie the \
  copy to that festival naturally rather than ignoring it.
- "hashtags": 5-10 relevant tags, mix of niche and broad, no leading '#' \
  and no spaces (e.g. "handmadeindia", not "#handmade india").
- "reel_script": a short beat-by-beat script (3-5 beats) ONLY when that \
  slot's type is "reel"; null for every other type.
- "carousel_slides": 3-6 short slide texts ONLY when that slot's type is \
  "carousel"; null for every other type.
- "image_prompt": a standalone image-generation prompt for this specific \
  post, referencing the brand's palette and tone — this feeds \
  app.ai.image.generate_image() directly.
- "cta": a short action phrase specific to this slot (not a generic \
  "Shop now" repeated everywhere).
"""


def build_user_message(
    profile: BusinessProfile,
    brand: BrandKit,
    slots: list[ScheduledSlot],
    *,
    campaign_focus: CampaignFocus = "general",
    campaign_note: str | None = None,
) -> str:
    products_block = (
        "\n".join(f"- {p.name}: {p.description}" for p in profile.products)
        or "No specific products listed."
    )
    slots_block = "\n".join(
        f"{i + 1}. {slot.date.isoformat()} · {slot.platform} · {slot.type}"
        + (f" · festival: {slot.festival}" if slot.festival else "")
        for i, slot in enumerate(slots)
    )
    focus_block = ""
    instruction = _CAMPAIGN_FOCUS_INSTRUCTIONS.get(campaign_focus)
    if instruction:
        focus_block = f"\n{instruction}"
        if campaign_note:
            focus_block += f"\nCampaign details: {campaign_note}"
        focus_block += "\n"
    return (
        f"Business name: {profile.name}\n"
        f"Business type: {profile.business_type}\n"
        f"Target audience: {profile.target_audience}\n"
        f"Location: {profile.location}\n\n"
        f"Products/services:\n{products_block}\n"
        f"{focus_block}\n"
        f"Brand voice tone: {brand.voice.tone}\n"
        f"Brand voice keywords: {', '.join(brand.voice.keywords) or 'not specified'}\n"
        f"Brand tagline: {brand.tagline}\n\n"
        f"Scheduled slots (write copy for each, in order):\n{slots_block}"
    )


REGENERATE_SYSTEM_PROMPT = """You are the Content Calendar copywriter for \
Sakhi, an AI business companion for Indian women micro-entrepreneurs. You \
are given a business profile, its brand kit, and ONE already-scheduled \
post slot (date, platform, post type, and — if applicable — a festival it \
falls near). You do NOT choose the date, platform, or post type — those \
are already fixed. Your only job is to write fresh copy for this one slot, \
optionally following the requester's specific instructions for the rewrite.

Respond with a single JSON object matching exactly this shape:

{
  "caption": string,
  "hashtags": [string],
  "reel_script": string or null,
  "carousel_slides": [string] or null,
  "image_prompt": string,
  "cta": string
}

Rules:
- Write in the brand's established voice (tone + keywords).
- Ground the caption in the business's actual products; never invent a \
  product that isn't listed. If a festival is noted, tie the copy to it \
  naturally.
- "hashtags": 5-10 relevant tags, mix of niche and broad, no leading '#' \
  and no spaces.
- "reel_script": a short beat-by-beat script (3-5 beats) ONLY if the slot's \
  type is "reel"; null otherwise.
- "carousel_slides": 3-6 short slide texts ONLY if the slot's type is \
  "carousel"; null otherwise.
- "image_prompt": a standalone image-generation prompt referencing the \
  brand's palette and tone.
- "cta": a short, specific action phrase, not a generic "Shop now".
- If the requester gave rewrite instructions, follow them precisely while \
  staying grounded in the rules above.
"""


def build_regenerate_user_message(
    profile: BusinessProfile,
    brand: BrandKit,
    slot: ScheduledSlot,
    *,
    instructions: str | None = None,
) -> str:
    products_block = (
        "\n".join(f"- {p.name}: {p.description}" for p in profile.products)
        or "No specific products listed."
    )
    slot_block = f"{slot.date.isoformat()} · {slot.platform} · {slot.type}" + (
        f" · festival: {slot.festival}" if slot.festival else ""
    )
    return (
        f"Business name: {profile.name}\n"
        f"Business type: {profile.business_type}\n"
        f"Target audience: {profile.target_audience}\n"
        f"Location: {profile.location}\n\n"
        f"Products/services:\n{products_block}\n\n"
        f"Brand voice tone: {brand.voice.tone}\n"
        f"Brand voice keywords: {', '.join(brand.voice.keywords) or 'not specified'}\n"
        f"Brand tagline: {brand.tagline}\n\n"
        f"Slot to rewrite: {slot_block}\n"
        f"Rewrite instructions: {instructions or 'None given — just write a strong fresh version.'}"
    )
