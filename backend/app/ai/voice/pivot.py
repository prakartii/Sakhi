"""Optional translate-to-English pivot strategy (settings.VOICE_TRANSLATE_PIVOT).

Default path (should_pivot() == False) is transcribe-in-her-language ->
pass that text to Groq with a same-language system instruction ->
synthesize the reply in that language — lower latency, no extra hops.

should_pivot() only decides *whether* pivoting is warranted for a given
language; it's a pure, deterministic rule (no LLM, no network), same
"rules decide structure" principle as the rest of app.ai. The actual
translate call (SarvamVoiceProvider.translate()) and the Groq round-trip
are composed by a future higher-level pipeline — this module doesn't call
either, keeping app.ai.voice unaware of app.ai.providers/Groq entirely.
"""

from __future__ import annotations

_ENGLISH_LANGUAGE = "en-IN"


def should_pivot(language: str, *, translate_pivot_enabled: bool) -> bool:
    """Whether `language` should be translated to English before Groq (and
    back before TTS). Never true for English itself — there's nothing to
    pivot — regardless of the flag.
    """
    return translate_pivot_enabled and language != _ENGLISH_LANGUAGE
