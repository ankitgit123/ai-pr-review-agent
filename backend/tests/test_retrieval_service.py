
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
