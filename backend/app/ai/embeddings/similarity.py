"""Cosine similarity ranking over embedding vectors — deterministic math,
no LLM, same principle as app.ai.forecasting and app.ai.rules.

Once memory_embeddings.embedding is populated, the real ANN retrieval for
production queries happens in Postgres via pgvector's <=> operator against
the ivfflat index (see migration 19) — that scales to the whole table.
This is for ranking a smaller, already-fetched candidate set in Python
(re-ranking a shortlist, or tests without a live database).
"""

from __future__ import annotations

import math

from app.ai.embeddings.schemas import CandidateVector, SimilarityMatch


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError(f"Vector length mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def top_k_similar(
    query: list[float],
    candidates: list[CandidateVector],
    *,
    k: int = 5,
) -> list[SimilarityMatch]:
    scored = [
        SimilarityMatch(id=c.id, score=cosine_similarity(query, c.embedding)) for c in candidates
    ]
    scored.sort(key=lambda match: match.score, reverse=True)
    return scored[:k]
