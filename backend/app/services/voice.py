"""Orchestrates one Companion voice turn end to end.

Not a new AI capability — this composes five already-built app.ai modules
(voice STT/TTS, voice_parsing, embeddings, orchestrator) with three
already-built repositories (voice_log, business_memory, conversation_history)
exactly the way each of their own docstrings says they're meant to be used
together. No AI module is modified; this is the caller they were all
waiting on.

Pipeline: audio bytes -> Sarvam STT -> transcript -> voice_parsing extracts
memory candidates + sentiment -> each memory is persisted and embedded ->
the orchestrator answers the transcript, grounded in brand/analytics facts
(if supplied) plus whatever past memories retrieval surfaces -> Sarvam TTS
speaks the answer -> both turns are written to conversation_history.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.memory_embedding import embed_memory_content
from app.ai.embeddings.persist import save_embedded_chunks
from app.ai.orchestrator.orchestrator import handle as orchestrate
from app.ai.providers.base import AIProviderError
from app.ai.voice.base import VoiceProviderError
from app.ai.voice.factory import get_voice_provider
from app.ai.voice_parsing.parser import parse_voice_transcript
from app.models.business_memory import BusinessMemory
from app.models.business_profile import BusinessProfile
from app.models.conversation_history import ConversationHistory
from app.models.enums import ConversationMessageType, ConversationRole, MemorySource, MemoryType
from app.models.voice_log import VoiceLog
from app.repositories.business_memory import BusinessMemoryRepository
from app.repositories.business_profile import BusinessProfileRepository
from app.repositories.conversation_history import ConversationHistoryRepository
from app.repositories.voice_log import VoiceLogRepository
from app.schemas.voice import MemoryOut, VoiceConverseResponse
from app.services.ai_mapping import to_ai_business_profile
from app.services.business_profile import BusinessProfileNotFoundError


class VoiceConversationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._profiles = BusinessProfileRepository(session)
        self._voice_logs = VoiceLogRepository(session)
        self._memories = BusinessMemoryRepository(session)
        self._conversation = ConversationHistoryRepository(session)

    async def converse(
        self,
        *,
        user_id: uuid.UUID,
        business_profile_id: uuid.UUID,
        audio: bytes,
        language: str,
        session_id: uuid.UUID | None,
    ) -> VoiceConverseResponse:
        profile = await self._get_owned_profile(business_profile_id, user_id)
        turn_session_id = session_id or uuid.uuid4()

        voice_provider = get_voice_provider()
        transcription = await voice_provider.transcribe(audio, language)

        voice_log = await self._voice_logs.create(
            VoiceLog(
                business_profile_id=profile.id,
                user_id=user_id,
                # Audio is processed in-memory for this pipeline, not
                # archived to object storage — see integration notes.
                audio_storage_path=f"transient/{uuid.uuid4()}",
                transcript=transcription.text,
                transcript_confidence=transcription.confidence,
            )
        )

        parsed = await parse_voice_transcript(transcription.text, language=language)
        voice_log.sentiment = parsed.sentiment

        memory_rows: list[BusinessMemory] = []
        for item in parsed.memories:
            memory = await self._memories.create(
                BusinessMemory(
                    business_profile_id=profile.id,
                    source_voice_log_id=voice_log.id,
                    memory_type=MemoryType(item.memory_type),
                    title=item.title,
                    content=item.content,
                    source=MemorySource.VOICE,
                    importance_score=item.importance_score,
                    occurred_at=_parse_occurred_at(item.occurred_at),
                )
            )
            memory_rows.append(memory)

        # Flush so the memories above have real ids before embedding them,
        # and so retrieval (below, via the orchestrator) can see them if a
        # later turn in the same request ever needed to (it can't today,
        # but keeps the ordering correct either way).
        await self._session.flush()
        for memory in memory_rows:
            try:
                chunks = await embed_memory_content(memory.content)
                await save_embedded_chunks(self._session, memory.id, chunks)
            except AIProviderError:
                # The memory itself is already saved (flushed above) —
                # only semantic recall of it is degraded, not lost, if the
                # embeddings provider is unavailable/misconfigured.
                pass

        ai_profile = to_ai_business_profile(profile)
        # Reply in whatever Sarvam actually detected (falling back to the
        # requested `language`) so the text handed to synthesize() below
        # matches the voice/language it's spoken in — see prompts.py's
        # LANGUAGE_NAMES for why this matters (a mismatch makes TTS read
        # English text with the wrong language's pronunciation rules).
        reply_language = transcription.detected_language or language
        try:
            orchestrator_response = await orchestrate(
                transcription.text,
                ai_profile,
                session=self._session,
                language=reply_language,
            )
        except AIProviderError:
            # Same embeddings-provider failure can surface here too, via
            # the orchestrator's own retrieval step — retry once without a
            # session so reasoning still happens, just ungrounded in past
            # memory for this turn.
            orchestrator_response = await orchestrate(
                transcription.text, ai_profile, language=reply_language
            )

        await self._conversation.create(
            ConversationHistory(
                business_profile_id=profile.id,
                user_id=user_id,
                session_id=turn_session_id,
                role=ConversationRole.USER,
                message_type=ConversationMessageType.VOICE,
                content=transcription.text,
                related_voice_log_id=voice_log.id,
            )
        )
        await self._conversation.create(
            ConversationHistory(
                business_profile_id=profile.id,
                user_id=user_id,
                session_id=turn_session_id,
                role=ConversationRole.ASSISTANT,
                message_type=ConversationMessageType.TEXT,
                content=orchestrator_response.answer,
            )
        )

        audio_base64: str | None = None
        audio_format = "wav"
        try:
            synthesis = await voice_provider.synthesize(orchestrator_response.answer, reply_language)
            audio_format = synthesis.format
            if synthesis.audio_bytes is not None:
                import base64

                audio_base64 = base64.b64encode(synthesis.audio_bytes).decode("ascii")
        except VoiceProviderError:
            # Reasoning already succeeded — a TTS hiccup shouldn't erase the
            # rest of the turn. The frontend falls back to text-only.
            pass

        await self._session.commit()

        return VoiceConverseResponse(
            voice_log_id=voice_log.id,
            session_id=turn_session_id,
            transcript=transcription.text,
            detected_language=transcription.detected_language,
            sentiment=parsed.sentiment,
            memories=[MemoryOut.model_validate(m) for m in memory_rows],
            answer=orchestrator_response.answer,
            used_services=orchestrator_response.used_services,
            sources=orchestrator_response.sources,
            audio_base64=audio_base64,
            audio_format=audio_format,
        )

    async def _get_owned_profile(
        self, business_profile_id: uuid.UUID, user_id: uuid.UUID
    ) -> BusinessProfile:
        profile = await self._profiles.get_by_id(business_profile_id)
        if profile is None or profile.user_id != user_id:
            raise BusinessProfileNotFoundError(
                f"Business profile {business_profile_id} not found."
            )
        return profile


def _parse_occurred_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
