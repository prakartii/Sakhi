"""Unit tests for cosine_similarity() and top_k_similar()."""

import pytest

from app.ai.embeddings.schemas import CandidateVector
from app.ai.embeddings.similarity import cosine_similarity, top_k_similar


def test_identical_vectors_have_similarity_one() -> None:
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_orthogonal_vectors_have_similarity_zero() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_opposite_vectors_have_similarity_negative_one() -> None:
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_zero_vector_returns_zero_not_a_division_error() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0


def test_mismatched_lengths_raise() -> None:
    with pytest.raises(ValueError):
        cosine_similarity([1.0, 2.0], [1.0])


def test_top_k_similar_ranks_and_truncates() -> None:
    query = [1.0, 0.0]
    candidates = [
        CandidateVector(id="close", embedding=[0.9, 0.1]),
        CandidateVector(id="far", embedding=[0.0, 1.0]),
        CandidateVector(id="opposite", embedding=[-1.0, 0.0]),
    ]

    results = top_k_similar(query, candidates, k=2)

    assert [r.id for r in results] == ["close", "far"]
    assert results[0].score > results[1].score
