
import math

import pytest

from app.services.document_chunker import DocumentChunk
from app.services.embedding_service import (
    EmbeddedChunk,
    EmbeddingService,
)


def test_real_embedding_has_384_finite_dimensions():
    service = EmbeddingService()

    vectors = service.embed_texts(
        ["Use the documented CSS layering token."]
    )

    assert len(vectors) == 1
    assert len(vectors[0]) == 384
    assert all(math.isfinite(value) for value in vectors[0])


def test_cosine_similarity_for_identical_vectors():
    score = EmbeddingService.cosine_similarity(
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
    )

    assert score == pytest.approx(1.0)


def test_cosine_similarity_for_orthogonal_vectors():
    score = EmbeddingService.cosine_similarity(
        [1.0, 0.0],
        [0.0, 1.0],
    )

    assert score == pytest.approx(0.0)


def test_cosine_similarity_rejects_mismatched_dimensions():
    with pytest.raises(ValueError, match="same dimensions"):
        EmbeddingService.cosine_similarity(
            [1.0, 0.0],
            [1.0, 0.0, 0.0],
        )


def test_ranking_places_relevant_chunk_first(monkeypatch):
    # Predetermined vectors make this a stable test of ranking logic.
    service = EmbeddingService.__new__(EmbeddingService)

    query_vector = [1.0, 0.0]
    monkeypatch.setattr(
        service,
        "embed_query",
        lambda query: query_vector,
    )

    css_chunk = DocumentChunk(
        chunk_id="css:header:1",
        source="css-layering-guidelines.md",
        section="Header",
        content="Use the documented CSS layering token.",
    )

    security_chunk = DocumentChunk(
        chunk_id="security:credentials:1",
        source="security-review-rules.md",
        section="Credentials",
        content="Database credentials must be protected.",
    )

    embedded_chunks = [
        EmbeddedChunk(chunk=security_chunk, vector=[0.0, 1.0]),
        EmbeddedChunk(chunk=css_chunk, vector=[0.99, 0.01]),
    ]

    ranked = service.rank_chunks(
        "What rules apply to header layering?",
        embedded_chunks,
    )

    assert ranked[0][0].chunk.chunk_id == "css:header:1"
    assert ranked[1][0].chunk.chunk_id == "security:credentials:1"
    assert ranked[0][1] > ranked[1][1]
