"""Writes embed_memory_content()'s output into memory_embeddings.

Raw SQL, matching retrieve.py's approach: the `embedding` column is a
pgvector `vector(1536)`, and this app doesn't depend on the `pgvector`
Python package for a SQLAlchemy column type, so inserts go through the same
cast-a-text-literal-to-vector pattern retrieve.py uses for reads.
"""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings.schemas import EmbeddedChunk

_INSERT_SQL = text(
    """
    insert into memory_embeddings
        (business_memory_id, chunk_index, chunk_text, embedding, embedding_model)
    values
        (cast(:business_memory_id as uuid), :chunk_index, :chunk_text,
         cast(:embedding as vector), :embedding_model)
    """
)


async def save_embedded_chunks(
    session: AsyncSession,
    business_memory_id: uuid.UUID,
    chunks: list[EmbeddedChunk],
) -> None:
    """Insert one memory_embeddings row per chunk. Caller owns commit."""
    for chunk in chunks:
        await session.execute(
            _INSERT_SQL,
            {
                "business_memory_id": str(business_memory_id),
                "chunk_index": chunk.chunk_index,
                "chunk_text": chunk.chunk_text,
                "embedding": _to_pgvector_literal(chunk.embedding),
                "embedding_model": chunk.embedding_model,
            },
        )


def _to_pgvector_literal(vector: list[float]) -> str:
    return "[" + ",".join(repr(v) for v in vector) + "]"
