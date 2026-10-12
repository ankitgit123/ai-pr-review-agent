
import math
from dataclasses import dataclass

from fastembed import TextEmbedding

from app.services.document_chunker import DocumentChunk


@dataclass(frozen=True)
class EmbeddedChunk:
    """A document chunk paired with its numerical embedding."""

    chunk: DocumentChunk
    vector: list[float]


class EmbeddingService:
    """Generate local embeddings and rank chunks by cosine similarity."""

    MODEL_NAME = "BAAI/bge-small-en-v1.5"

    def __init__(self) -> None:
        self.model = TextEmbedding(model_name=self.MODEL_NAME)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Convert a list of texts into vectors."""

        if not texts:
            return []

        vectors = self.model.embed(texts)
        return [vector.tolist() for vector in vectors]

    def embed_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> list[EmbeddedChunk]:
        """Embed chunk content while preserving its metadata."""

        vectors = self.embed_texts([chunk.content for chunk in chunks])

        return [
            EmbeddedChunk(chunk=chunk, vector=vector)
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]

    def embed_query(self, query: str) -> list[float]:
        """Generate a vector for a search query."""

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        return self.embed_texts([query])[0]

    @staticmethod
    def cosine_similarity(
        vector_a: list[float],
        vector_b: list[float],
    ) -> float:
        """Measure the cosine similarity between two vectors."""

        if len(vector_a) != len(vector_b):
            raise ValueError("Vectors must have the same dimensions.")

        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        magnitude_a = math.sqrt(sum(a * a for a in vector_a))
        magnitude_b = math.sqrt(sum(b * b for b in vector_b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def rank_chunks(
        self,
        query: str,
        embedded_chunks: list[EmbeddedChunk],
    ) -> list[tuple[EmbeddedChunk, float]]:
        """Rank embedded chunks from most to least similar to a query."""

        query_vector = self.embed_query(query)

        ranked = [
            (
                item,
                self.cosine_similarity(query_vector, item.vector),
            )
            for item in embedded_chunks
        ]

        return sorted(ranked, key=lambda item: item[1], reverse=True)
