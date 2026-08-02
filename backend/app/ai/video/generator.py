"""generate_video(): the public entry point for video generation. Every
call is a real, billed fal.ai request — see app.ai.video's package
docstring and provider.py's VideoProvider docstring. Callers must treat
this as a deliberate action a user explicitly opted into, never a side
effect of something else.
"""

from __future__ import annotations

from app.ai.video.factory import get_video_provider
from app.ai.video.models import GeneratedVideo
from app.ai.video.provider import VideoProvider


async def generate_video(prompt: str, *, provider: VideoProvider | None = None) -> GeneratedVideo:
    """Generate a short video from `prompt`.

    Raises ValueError on an empty prompt. Raises AIProviderRequestError /
    AIProviderResponseError (from app.ai.providers.base) on API/response
    failures from the underlying video provider.
    """
    if not prompt.strip():
        raise ValueError("prompt must not be empty")

    video_provider = provider or get_video_provider()
    url = await video_provider.generate(prompt.strip())

    return GeneratedVideo(url=url, provider=video_provider.name, prompt=prompt.strip())
