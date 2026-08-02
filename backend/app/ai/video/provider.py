"""Provider-agnostic video-generation interface — the video counterpart to
app.ai.image's ImageProvider. Not an LLM call. Implementations wrap one
vendor's video API; call sites depend on this interface, never a concrete
SDK, so swapping video vendors is a factory.py change.

Every implementation of this interface represents a real, billed API
call — unlike app.ai.image/embeddings, there is no free-tier vendor
option here (see app.ai.video's package docstring). Callers must treat
`generate()` as a deliberate, cost-incurring action, never something
triggered automatically as a side effect of another action.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class VideoProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier stored as GeneratedVideo.provider."""
        raise NotImplementedError

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate a short video from `prompt` and return its hosted URL.
        Real money is spent on every call — see this module's docstring."""
        raise NotImplementedError
