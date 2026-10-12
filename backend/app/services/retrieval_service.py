
from app.services.query_generation_service import QueryGenerationService
from app.services.vector_store_service import VectorStoreService


class RetrievalService:
    """Generate search queries and retrieve relevant coding standards."""

    def __init__(
        self,
        query_generation_service: QueryGenerationService | None = None,
        vector_store_service: VectorStoreService | None = None,
    ) -> None:
        self.query_generation_service = (
            query_generation_service or QueryGenerationService()
        )
        self.vector_store_service = vector_store_service or VectorStoreService()

    def retrieve(
        self,
        diff: str,
        top_k_per_query: int = 3,
        max_results: int = 5,
    ) -> list[dict]:
        """Retrieve and deduplicate policy chunks relevant to a PR diff."""

        if not diff or not diff.strip():
            return []

        if top_k_per_query <= 0:
            raise ValueError("top_k_per_query must be positive.")

        if max_results <= 0:
            raise ValueError("max_results must be positive.")

        queries = self.query_generation_service.generate_queries(diff)

        # Keep the best score for a chunk if multiple queries find it.
        results_by_chunk_id: dict[str, dict] = {}

        for query in queries:
            matches = self.vector_store_service.search(
                query=query,
                top_k=top_k_per_query,
            )

            for match in matches:
                chunk_id = match["chunk_id"]
                existing = results_by_chunk_id.get(chunk_id)

                if existing is None:
                    results_by_chunk_id[chunk_id] = {
                        **match,
                        "matched_queries": [query],
                    }
                else:
                    if query not in existing["matched_queries"]:
                        existing["matched_queries"].append(query)

                    if match["similarity"] > existing["similarity"]:
                        existing["similarity"] = match["similarity"]
                        existing["content"] = match["content"]
                        existing["source"] = match["source"]
                        existing["section"] = match["section"]

        ranked_results = sorted(
            results_by_chunk_id.values(),
            key=lambda result: result["similarity"],
            reverse=True,
        )

        return ranked_results[:max_results]
