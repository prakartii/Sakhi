"""Turns a raw voice-check-in transcript into structured business_memory
candidates + an overall sentiment, using the configured aiProvider's JSON
mode. Output shapes mirror business_memory / voice_logs.sentiment (see
supabase/migrations 06-07) so results can be persisted with no remapping.
"""

from __future__ import annotations

from datetime import date

from pydantic import ValidationError

from app.ai.providers import AIProvider, AIProviderResponseError, ChatMessage, get_ai_provider
from app.ai.voice_parsing.prompts import SYSTEM_PROMPT, build_user_message
from app.ai.voice_parsing.schemas import ParsedVoiceLog


async def parse_voice_transcript(
    transcript: str,
    *,
    language: str | None = None,
    reference_date: date | None = None,
    provider: AIProvider | None = None,
) -> ParsedVoiceLog:
    """Extract structured business-memory candidates from a raw transcript.

    `language` is the BCP-47 code the Web Speech API captured (e.g. "hi-IN",
    "ta-IN"), passed through as context — the transcript text itself is
    sent as-is regardless of language. `reference_date` anchors relative
    time expressions ("last week") and defaults to today.

    Raises ValueError on an empty transcript, and AIProviderResponseError
    if the model's output is empty, isn't valid JSON, or doesn't match the
    expected schema.
    """
    if not transcript.strip():
        raise ValueError("transcript must not be empty")

    ai = provider or get_ai_provider()
    messages: list[ChatMessage] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_message(
                transcript,
                language=language,
                reference_date=reference_date or date.today(),
            ),
        },
    ]

    raw = await ai.chat_json(messages, temperature=0.2)
    try:
        return ParsedVoiceLog.model_validate(raw)
    except ValidationError as exc:
        raise AIProviderResponseError(
            f"Voice parse result failed schema validation: {exc}"
        ) from exc
