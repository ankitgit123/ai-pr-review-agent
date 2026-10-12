
from app.services.document_chunker import MarkdownDocumentChunker
from app.services.document_loader import MarkdownDocumentLoader
from app.services.embedding_service import EmbeddingService


def main() -> None:
    # 1. Load and chunk the real Markdown knowledge files.
    loader = MarkdownDocumentLoader(
        "/app/knowledge/coding-standards"
    )
    documents = loader.load_documents()

    chunker = MarkdownDocumentChunker(
        max_chars=500,
        overlap_chars=50,
    )
    chunks = chunker.chunk_documents(documents)

    if not chunks:
        raise RuntimeError("No document chunks were loaded.")

    # 2. Generate embeddings for the actual chunks.
    service = EmbeddingService()
    embedded_chunks = service.embed_chunks(chunks)

    # 3. Embed a CSS-related query.
    query = (
        "What coding standards apply when changing "
        "the header's z-index and layering behavior?"
    )
    ranked = service.rank_chunks(query, embedded_chunks)

    print("Query:", query)
    print("\nRanked knowledge chunks:")

    for item, score in ranked:
        print(f"\nSimilarity: {score:.4f}")
        print("Source:", item.chunk.source)
        print("Section:", item.chunk.section)
        print("Chunk ID:", item.chunk.chunk_id)
        print("Content:", item.chunk.content[:200])

    # 4. Compare the query with an unrelated security passage.
    unrelated_text = (
        "Database connections must use secure credentials. "
        "Passwords should be stored in environment variables."
    )
    unrelated_vector = service.embed_query(unrelated_text)
    query_vector = service.embed_query(query)

    unrelated_score = service.cosine_similarity(
        query_vector,
        unrelated_vector,
    )

    print("\nUnrelated database-security comparison:")
    print(f"Similarity: {unrelated_score:.4f}")

    print("\nEmbedding and ranking test completed.")


if __name__ == "__main__":
    main()
