import pytest
from app.services.retrieval_service import RetrievalService


class FakeQueryGenerationService:
    def generate_queries(self, diff: str) -> list[str]:
        return ["header layering rules", "overlay interaction rules"]


class FakeVectorStoreService:
    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if query == "header layering rules":
            return [
                {
                    "chunk_id": "header",
                    "content": "Use the documented layering token.",
                    "source": "css-layering-guidelines.md",
                    "section": "CSS Layering Guidelines > Header",
                    "similarity": 0.80,
                },
                {
                    "chunk_id": "overlays",
                    "content": "Verify overlay interactions.",
                    "source": "css-layering-guidelines.md",
                    "section": "CSS Layering Guidelines > Overlays",
                    "similarity": 0.65,
                },
            ]

        return [
            {
                "chunk_id": "overlays",
                "content": "Verify overlay interactions.",
                "source": "css-layering-guidelines.md",
                "section": "CSS Layering Guidelines > Overlays",
                "similarity": 0.72,
            },
            {
                "chunk_id": "modals",
                "content": "Modals must appear above page content.",
                "source": "css-layering-guidelines.md",
                "section": "CSS Layering Guidelines > Modal Dialogs",
                "similarity": 0.68,
            },
        ]


def test_retrieves_and_deduplicates_chunks():
    service = RetrievalService(
        query_generation_service=FakeQueryGenerationService(),
        vector_store_service=FakeVectorStoreService(),
    )

    results = service.retrieve("sample PR diff")

    assert [result["chunk_id"] for result in results] == [
        "header",
        "overlays",
        "modals",
    ]
    assert results[1]["similarity"] == 0.72
    assert len(results[1]["matched_queries"]) == 2


def test_empty_diff_returns_no_results():
    service = RetrievalService(
        query_generation_service=FakeQueryGenerationService(),
        vector_store_service=FakeVectorStoreService(),
    )

    assert service.retrieve("") == []


def test_rejects_invalid_top_k():
    service = RetrievalService(
        query_generation_service=FakeQueryGenerationService(),
        vector_store_service=FakeVectorStoreService(),
    )

    try:
        service.retrieve("sample diff", top_k_per_query=0)
    except ValueError as exc:
        assert "top_k_per_query" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_respects_max_results():
    service = RetrievalService(
        query_generation_service=FakeQueryGenerationService(),
        vector_store_service=FakeVectorStoreService(),
    )

    results = service.retrieve("sample diff", max_results=2)

    assert len(results) == 2
    assert [result["chunk_id"] for result in results] == [
        "header",
        "overlays",
    ]


def test_rejects_invalid_max_results():
    service = RetrievalService(
        query_generation_service=FakeQueryGenerationService(),
        vector_store_service=FakeVectorStoreService(),
    )

    with pytest.raises(ValueError, match="max_results"):
        service.retrieve("sample diff", max_results=0)


def test_returns_empty_when_no_queries_are_generated():
    class NoQueries:
        def generate_queries(self, diff: str) -> list[str]:
            return []

    service = RetrievalService(
        query_generation_service=NoQueries(),
        vector_store_service=FakeVectorStoreService(),
    )

    assert service.retrieve("sample diff") == []


def test_returns_empty_when_vector_search_finds_no_matches():
    class NoMatches:
        def search(self, query: str, top_k: int = 3) -> list[dict]:
            return []

    service = RetrievalService(
        query_generation_service=FakeQueryGenerationService(),
        vector_store_service=NoMatches(),
    )

    assert service.retrieve("sample diff") == []


def test_passes_top_k_to_vector_search():
    class RecordingVectorStore:
        def __init__(self):
            self.calls = []

        def search(self, query: str, top_k: int = 3) -> list[dict]:
            self.calls.append((query, top_k))
            return []

    vector_store = RecordingVectorStore()
    service = RetrievalService(
        query_generation_service=FakeQueryGenerationService(),
        vector_store_service=vector_store,
    )

    service.retrieve("sample diff", top_k_per_query=2)

    assert vector_store.calls == [
        ("header layering rules", 2),
        ("overlay interaction rules", 2),
    ]


def test_keeps_best_matching_chunk_content_and_metadata():
    class ChangingMatches:
        def search(self, query: str, top_k: int = 3) -> list[dict]:
            if query == "header layering rules":
                return [
                    {
                        "chunk_id": "shared",
                        "content": "Lower-ranked content",
                        "source": "old.md",
                        "section": "Old section",
                        "similarity": 0.60,
                    }
                ]

            return [
                {
                    "chunk_id": "shared",
                    "content": "Best matching content",
                    "source": "coding-standards.md",
                    "section": "Security > Authorization",
                    "similarity": 0.90,
                }
            ]

    service = RetrievalService(
        query_generation_service=FakeQueryGenerationService(),
        vector_store_service=ChangingMatches(),
    )

    results = service.retrieve("sample diff")

    assert len(results) == 1
    assert results[0]["content"] == "Best matching content"
    assert results[0]["source"] == "coding-standards.md"
    assert results[0]["section"] == "Security > Authorization"
    assert results[0]["similarity"] == 0.90
    assert len(results[0]["matched_queries"]) == 2

