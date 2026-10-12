
from app.integrations.github.client import GitHubClient
from app.services.query_generation_service import QueryGenerationService
from app.services.retrieval_service import RetrievalService


def main() -> None:
    owner = "ankitgit123"
    repository = "book-worm"
    pull_request_number = 1

    # Fetch the real PR diff from GitHub (read-only).
    github_client = GitHubClient()
    diff = github_client.get_pull_request_diff(
        owner=owner,
        repository=repository,
        pull_request_number=pull_request_number,
    )

    print(f"PR: {owner}/{repository}#{pull_request_number}")
    print(f"Diff characters: {len(diff)}")

    # Inspect the generated queries.
    query_service = QueryGenerationService()
    queries = query_service.generate_queries(diff)

    print(f"\nGenerated queries: {len(queries)}")
    for index, query in enumerate(queries, start=1):
        print(f"{index}. {query}")

    # Retrieve evidence from the real persistent Chroma collection.
    retrieval_service = RetrievalService()
    results = retrieval_service.retrieve(
        diff=diff,
        top_k_per_query=3,
        max_results=5,
    )

    print(f"\nRetrieved unique chunks: {len(results)}")

    for index, result in enumerate(results, start=1):
        print(f"\n--- Result {index} ---")
        print(f"Section: {result['section']}")
        print(f"Source: {result['source']}")
        print(f"Similarity: {result['similarity']:.4f}")
        print(f"Matched queries: {result['matched_queries']}")
        print(f"Content:\n{result['content']}")


if __name__ == "__main__":
    main()
