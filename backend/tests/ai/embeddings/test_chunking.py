"""Unit tests for chunk_text()."""

import pytest

from app.ai.embeddings.chunking import chunk_text


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_short_text_returns_single_chunk() -> None:
    chunks = chunk_text("Raised dupatta price to Rs 820.", max_words=200, overlap_words=30)

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == "Raised dupatta price to Rs 820."


def test_long_text_splits_with_overlap() -> None:
    words = [f"word{i}" for i in range(25)]
    text = " ".join(words)

    chunks = chunk_text(text, max_words=10, overlap_words=3)

    assert len(chunks) > 1
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    # Every word appears somewhere, and consecutive chunks share the overlap.
    assert chunks[0].text.split() == words[0:10]
    assert chunks[1].text.split() == words[7:17]
    assert chunks[-1].text.split()[-1] == words[-1]


def test_rejects_invalid_window_sizes() -> None:
    with pytest.raises(ValueError):
        chunk_text("some text here", max_words=0)
    with pytest.raises(ValueError):
        chunk_text("some text here", max_words=10, overlap_words=10)
    with pytest.raises(ValueError):
        chunk_text("some text here", max_words=10, overlap_words=-1)
