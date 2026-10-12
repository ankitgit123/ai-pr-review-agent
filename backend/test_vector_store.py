
from app.services.document_loader import MarkdownDocumentLoader
from app.services.document_chunker import MarkdownDocumentChunker
from app.services.vector_store_service import VectorStoreService


def main() -> None:
    # 1. Load the coding-standard Markdown files.
    loader = MarkdownDocumentLoader("/app/knowledge/coding-standards")
    documents = loader.load_documents()

    # 2. Split documents into meaningful chunks.
    chunker = MarkdownDocumentChunker()
    chunks = chunker.chunk_documents(documents)

    print(f"Documents loaded: {len(documents)}")
    print(f"Chunks to index: {len(chunks)}")

    # 3. Generate embeddings and store the chunks in Chroma.
    vector_store = VectorStoreService()
    vector_store.index_chunks(chunks)

    print("Indexing completed.")

    # 4. Search using a realistic PR-review question.
    query = "What should I verify when increasing the header's z-index?"
    results = vector_store.search(query, top_k=3)

    print(f"\nQuery: {query}")
    print(f"Results returned: {len(results)}")

    for index, result in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print(f"Source: {result['source']}")
        print(f"Section: {result['section']}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Content:\n{result['content']}")


if __name__ == "__main__":
    main()
