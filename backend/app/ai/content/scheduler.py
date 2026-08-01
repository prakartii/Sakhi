"""Deterministic content-calendar scheduling: picks dates, platforms,
post types, and post times for a month. No LLM, no randomness — the same
inputs always produce the same schedule. app.ai.content.generator fills
in copy for each slot afterward; this module only decides the slots.
"""

from __future__ import annotations

import calendar
from datetime import date, time

from app.ai.content.models import PostType, ScheduledSlot

DEFAULT_POSTS_PER_WEEK = 3

# Cycled per slot, not randomized, so the same schedule is reproducible.
_POST_TYPE_CYCLE: list[PostType] = ["post", "reel", "carousel", "post", "reel", "story", "post"]

_PLATFORM_BEST_TIMES: dict[str, time] = {
    "instagram": time(19, 0),
    "facebook": time(13, 0),
    "whatsapp": time(10, 0),
    "linkedin": time(9, 0),
}
_DEFAULT_POST_TIME = time(18, 0)

# Only true fixed-Gregorian-date festivals are included here. Diwali,
# Holi, Raksha Bandhan, Eid etc. follow the lunar calendar and shift every
# year — approximating them would misdate real posts, so they're
# deliberately left out of this deterministic layer rather than guessed.
# A production version would look these up from a proper Indian festival
# calendar API/library instead.
FIXED_DATE_FESTIVALS: dict[tuple[int, int], str] = {
    (1, 26): "Republic Day",
    (8, 15): "Independence Day",
    (10, 2): "Gandhi Jayanti",
    (12, 25): "Christmas",
}


def schedule_month(
    month: date,
    platforms: list[str],
    *,
    posts_per_week: int = DEFAULT_POSTS_PER_WEEK,
) -> list[ScheduledSlot]:
    """Deterministically pick (date, platform, type, post_time, festival)
    slots for the calendar month containing `month` (only its year/month
    are used — the day is ignored).

    Posts are spread evenly across the month at roughly `posts_per_week`
    per week, cycling through `platforms` and a fixed post-type mix.
    """
    if not platforms:
        raise ValueError("platforms must not be empty")
    if posts_per_week < 1:
        raise ValueError("posts_per_week must be >= 1")

    days_in_month = calendar.monthrange(month.year, month.month)[1]
    all_dates = [date(month.year, month.month, day) for day in range(1, days_in_month + 1)]

    step = max(1, round(7 / posts_per_week))
    post_dates = all_dates[::step]

    slots: list[ScheduledSlot] = []
    for i, d in enumerate(post_dates):
        platform = platforms[i % len(platforms)]
        post_type = _POST_TYPE_CYCLE[i % len(_POST_TYPE_CYCLE)]
        post_time = _PLATFORM_BEST_TIMES.get(platform.lower(), _DEFAULT_POST_TIME)
        festival = FIXED_DATE_FESTIVALS.get((d.month, d.day))
        slots.append(
            ScheduledSlot(date=d, platform=platform, type=post_type, post_time=post_time, festival=festival)
        )
    return slots
