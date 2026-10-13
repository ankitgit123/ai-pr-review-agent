
from app.services.llm_review_service import (
    LLMReviewFinding,
    LLMReviewResult,
    LLMReviewService,
)


def make_finding(
    *,
    rule_id: str = "LLM001",
    message: str = "Potential null dereference.",
) -> LLMReviewFinding:
    return LLMReviewFinding(
        rule_id=rule_id,
        severity="high",
        category="bug",
        classification="evidence_backed",
        message=message,
        file_path="frontend/src/api.ts",
        line_number=2,
        evidence="return fetchProfile(userId);",
        evidence_explanation="The changed line may propagate a rejected promise.",
        policy_sources=[],
    )


def test_removes_exact_duplicate_findings():
    first = make_finding()
    duplicate = make_finding()

    result = LLMReviewResult(
        findings=[first, duplicate],
        summary="Two findings reported.",
    )

    deduplicated = LLMReviewService._deduplicate_findings(result)

    assert deduplicated.findings == [first]
    assert len(deduplicated.findings) == 1


def test_preserves_distinct_findings():
    first = make_finding()
    second = make_finding(
        rule_id="LLM002",
        message="A different potential issue.",
    )

    result = LLMReviewResult(
        findings=[first, second],
        summary="Two distinct findings.",
    )

    deduplicated = LLMReviewService._deduplicate_findings(result)

    assert deduplicated.findings == [first, second]
