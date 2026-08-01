"""High-level helper: chunk a business_memory.content string and embed each
chunk, producing rows ready to persist into memory_embeddings (see
supabase/migrations/07_business_memory_and_embeddings.sql + migration 19).
Chunking/embedding and persistence stay separate — this returns data,
callers own writing it to the database.
"""

from __future__ import annotations

from app.ai.embeddings.chunking import DEFAULT_MAX_WORDS, DEFAULT_OVERLAP_WORDS, chunk_text
from app.ai.embeddings.factory import get_embedding_provider
from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.embeddings.schemas import EmbeddedChunk


async def embed_memory_content(
    content: str,
    *,
    max_words: int = DEFAULT_MAX_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
    provider: EmbeddingProvider | None = None,
) -> list[EmbeddedChunk]:
    """Chunk `content` and embed every chunk. Returns [] for empty content."""
    chunks = chunk_text(content, max_words=max_words, overlap_words=overlap_words)
    if not chunks:
        return []

    embedder = provider or get_embedding_provider()
    vectors = await embedder.embed([chunk.text for chunk in chunks])

    return [
        EmbeddedChunk(
            chunk_index=chunk.chunk_index,
            chunk_text=chunk.text,
            embedding=vector,
            embedding_model=embedder.model_name,
        )
        for chunk, vector in zip(chunks, vectors)
    ]
