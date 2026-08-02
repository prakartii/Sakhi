"""Video generation — fal.ai by default (settings.VIDEO_PROVIDER).

Deliberately separate from app.ai.image: there is no free-tier video
vendor available to this app the way Together/Gemini are free (or
free-enough) for images. fal.ai gives a one-time signup credit and then
bills per second of output — see app.ai.video.provider.VideoProvider's
docstring. Every call through generate_video() is a real, billed request;
callers (endpoints, frontend buttons) must make that a distinct, explicit
action, never bundled automatically into another flow.
"""

from app.ai.video.factory import get_video_provider
from app.ai.video.generator import generate_video
from app.ai.video.models import GeneratedVideo
from app.ai.video.provider import VideoProvider

__all__ = ["GeneratedVideo", "VideoProvider", "generate_video", "get_video_provider"]
