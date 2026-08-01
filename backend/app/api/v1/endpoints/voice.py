"""POST /voice/converse — the Companion page's one call: upload a voice
recording, get back a transcript, extracted memories, a grounded AI reply,
and spoken audio of that reply. See app.services.voice for the pipeline;
this endpoint only handles the multipart upload and auth/ownership.

POST /voice/transcribe — a lighter STT-only call for contexts that need a
transcript but have no business_profile_id yet to ground a full converse
turn in, e.g. Business Setup's mic button (recorded speech -> story
textarea, before any business profile exists to converse against).
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import AIProviderError
from app.ai.voice.base import VoiceProviderError
from app.ai.voice.factory import get_voice_provider
from app.api.deps import get_current_app_user, get_db_session
from app.models.user import User
from app.schemas.voice import TranscribeResponse, VoiceConverseResponse
from app.services.business_profile import BusinessProfileNotFoundError
from app.services.voice import VoiceConversationService

router = APIRouter()


@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="Speech-to-text only, no business profile required",
    responses={
        422: {"description": "Empty audio upload, or the provider returned an empty transcript"},
        503: {"description": "Voice provider unavailable"},
    },
)
async def transcribe(
    language: str = Form("en-IN"),
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_app_user),
) -> TranscribeResponse:
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Uploaded audio was empty.")

    try:
        result = await get_voice_provider().transcribe(audio_bytes, language)
    except VoiceProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    return TranscribeResponse(
        transcript=result.text,
        detected_language=result.detected_language,
        confidence=result.confidence,
    )


@router.post(
    "/converse",
    response_model=VoiceConverseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="One voice turn: audio in, transcript + memories + spoken reply out",
    responses={
        404: {"description": "Business profile not found or not owned by the caller"},
        422: {"description": "Empty transcript, or AI output failed schema validation"},
        503: {"description": "Voice or reasoning provider unavailable"},
    },
)
async def converse(
    business_profile_id: uuid.UUID = Form(...),
    language: str = Form("en-IN"),
    session_id: uuid.UUID | None = Form(None),
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_app_user),
    db: AsyncSession = Depends(get_db_session),
) -> VoiceConverseResponse:
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Uploaded audio was empty.")

    service = VoiceConversationService(db)
    try:
        return await service.converse(
            user_id=current_user.id,
            business_profile_id=business_profile_id,
            audio=audio_bytes,
            language=language,
            session_id=session_id,
        )
    except BusinessProfileNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except AIProviderError as exc:
        # Covers config/request/response failures alike (e.g. Groq rate
        # limits raise AIProviderRequestError, not AIProviderResponseError)
        # — narrower handling here left rate-limit/network failures
        # unhandled, surfacing as a raw 500 with no CORS headers instead of
        # this clean 503.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
    except VoiceProviderError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
