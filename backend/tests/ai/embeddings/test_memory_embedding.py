"""Unit tests for embed_memory_content() — chunking + embedding wired
together, against a fake in-memory EmbeddingProvider (no real API calls)."""

from app.ai.embeddings.memory_embedding import embed_memory_content
from app.ai.embeddings.provider import EmbeddingProvider


class FakeEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    @property
    def model_name(self) -> str:
        return "fake-embedding-model"

    @property
    def dimensions(self) -> int:
        return 3

    async def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        # Deterministic per-text vector so assertions can check ordering.
        return [[float(len(t)), 0.0, 0.0] for t in texts]


async def test_embed_memory_content_empty_returns_empty() -> None:
    provider = FakeEmbeddingProvider()

    result = await embed_memory_content("", provider=provider)

    assert result == []
    assert provider.calls == []


async def test_embed_memory_content_single_chunk() -> None:
    provider = FakeEmbeddingProvider()

    result = await embed_memory_content(
        "Raised dupatta price from Rs 640 to Rs 820.", provider=provider
    )

    assert len(result) == 1
    assert result[0].chunk_index == 0
    assert result[0].chunk_text == "Raised dupatta price from Rs 640 to Rs 820."
    assert result[0].embedding_model == "fake-embedding-model"
    assert result[0].embedding == [len(result[0].chunk_text), 0.0, 0.0]


async def test_embed_memory_content_multiple_chunks_preserve_order() -> None:
    provider = FakeEmbeddingProvider()
    words = [f"word{i}" for i in range(25)]
    text = " ".join(words)

    result = await embed_memory_content(text, max_words=10, overlap_words=3, provider=provider)

    assert len(result) > 1
    assert [c.chunk_index for c in result] == list(range(len(result)))
    assert provider.calls == [[c.chunk_text for c in result]]
