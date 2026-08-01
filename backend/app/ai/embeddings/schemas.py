"""Pydantic schemas for embedding generation, chunking, and similarity
ranking. `EmbeddedChunk` mirrors memory_embeddings' columns exactly (see
supabase/migrations/07_business_memory_and_embeddings.sql and migration 19,
which adds the embedding column) so results can be persisted with no
remapping.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    chunk_index: int
    text: str


class EmbeddedChunk(BaseModel):
    chunk_index: int
    chunk_text: str
    embedding: list[float]
    embedding_model: str


class CandidateVector(BaseModel):
    """One already-fetched row to rank against a query vector — e.g. a
    memory_embeddings row's (id, embedding) pulled back from Postgres."""

    id: str
    embedding: list[float]


class SimilarityMatch(BaseModel):
    id: str
    score: float = Field(..., ge=-1, le=1, description="Cosine similarity; 1.0 = identical direction.")


class RetrievedMemory(BaseModel):
    """One business_memory row (via its matching chunk) returned by
    app.ai.embeddings.retrieve.retrieve(). similarity is computed by
    Postgres (pgvector's `<=>` operator), not recomputed in Python."""

    business_memory_id: str
    title: str | None
    content: str
    chunk_index: int
    chunk_text: str
    similarity: float = Field(..., ge=-1, le=1)
