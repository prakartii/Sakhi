"""Word-count-based text chunking for embedding generation. Deterministic,
no LLM/tokenizer dependency — business_memory.content is typically a
sentence or two (see the memory.tsx mock data), so most calls produce a
single chunk; longer content is split with overlap so no boundary loses
context.
"""

from __future__ import annotations

from app.ai.embeddings.schemas import Chunk

DEFAULT_MAX_WORDS = 200
DEFAULT_OVERLAP_WORDS = 30


def chunk_text(
    text: str,
    *,
    max_words: int = DEFAULT_MAX_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> list[Chunk]:
    """Split `text` into word-count-bounded chunks with `overlap_words` of
    repeated context between consecutive chunks. Returns [] for empty/
    whitespace-only input, and a single chunk (index 0) when `text` already
    fits within `max_words`.
    """
    if max_words <= 0:
        raise ValueError("max_words must be > 0")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be >= 0 and < max_words")

    words = text.split()
    if not words:
        return []
    if len(words) <= max_words:
        return [Chunk(chunk_index=0, text=text.strip())]

    step = max_words - overlap_words
    chunks: list[Chunk] = []
    start = 0
    index = 0
    while start < len(words):
        piece = words[start : start + max_words]
        chunks.append(Chunk(chunk_index=index, text=" ".join(piece)))
        if start + max_words >= len(words):
            break
        start += step
        index += 1
    return chunks
