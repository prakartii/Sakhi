"""Provider-agnostic chat interface every AI backend (Groq, Gemini, Ollama,
...) implements. Call sites depend on `AIProvider` and `ChatMessage` here,
never on a concrete vendor SDK — swapping providers is a factory.py change,
not a call-site change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Literal, TypedDict


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


class AIProviderError(Exception):
    """Base class for all aiProvider failures."""


class AIProviderConfigError(AIProviderError):
    """Raised when a provider is selected/constructed without valid
    configuration (e.g. AI_PROVIDER=groq but GROQ_API_KEY is unset)."""


class AIProviderRequestError(AIProviderError):
    """Raised when the underlying API call itself fails — network error,
    auth failure, rate limit, 5xx from the vendor."""


class AIProviderResponseError(AIProviderError):
    """Raised when a provider call succeeds but returns something callers
    can't use — empty content, or JSON that doesn't parse in chat_json()."""


class AIProvider(ABC):
    """Provider-agnostic chat interface. One implementation per LLM vendor."""

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Return the assistant's plain-text reply to `messages`."""
        raise NotImplementedError

    @abstractmethod
    async def chat_json(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Return the assistant's reply parsed as a JSON object.

        `messages` must itself instruct the model to respond with JSON —
        this only guarantees the response is *parsed* as JSON (enabling the
        provider's JSON mode where available and raising
        AIProviderResponseError on invalid output), it doesn't inject that
        instruction into the prompt.
        """
        raise NotImplementedError
