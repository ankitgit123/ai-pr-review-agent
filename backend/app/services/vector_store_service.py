
from pathlib import Path

import chromadb

from app.services.document_chunker import DocumentChunk
from app.services.embedding_service import (
    EmbeddedChunk,
    EmbeddingService,
)


class VectorStoreService:
    """Persist document chunks and search them by semantic similarity."""

    COLLECTION_NAME = "coding_standards"

    def __init__(
        self,
        persist_directory: str = "/app/data/chroma",
    ) -> None:
        Path(persist_directory).mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = chromadb.PersistentClient(
            path=persist_directory,
        )

        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        self.embedding_service = EmbeddingService()

    def index_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> int:
        """Generate embeddings and insert or update document chunks."""

        if not chunks:
            return 0

        embedded_chunks = self.embedding_service.embed_chunks(chunks)

        self.collection.upsert(
            ids=[item.chunk.chunk_id for item in embedded_chunks],
            documents=[
                item.chunk.content for item in embedded_chunks
            ],
            embeddings=[
                item.vector for item in embedded_chunks
            ],
            metadatas=[
                {
                    "source": item.chunk.source,
                    "section": item.chunk.section,
                }
                for item in embedded_chunks
            ],
        )

        return len(embedded_chunks)

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        """Retrieve the most relevant chunks for a query."""

        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        if self.collection.count() == 0:
            return []

        query_vector = self.embedding_service.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        matches: list[dict] = []

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for chunk_id, content, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
            strict=True,
        ):
            matches.append(
                {
                    "chunk_id": chunk_id,
                    "content": content,
                    "source": metadata["source"],
                    "section": metadata["section"],
                    # Chroma cosine distance is 1 - cosine similarity.
                    "similarity": 1.0 - distance,
                }
            )

        return matches
