
import pytest

from app.schemas.review_input import PullRequestData, ReviewInput
from app.services.llm_review_service import (
    LLMReviewFinding,
    LLMReviewResult,
    LLMReviewService,
    PolicySource,
)


class FakeModel:
    def __init__(self, response: LLMReviewResult) -> None:
        self.response = response

    def invoke(self, messages):
        return self.response


def make_review_input() -> ReviewInput:
    return ReviewInput(
        pull_request=PullRequestData(
            number=1,
            title="Increase header z-index",
            state="open",
            draft=False,
            html_url="https://github.com/example/repo/pull/1",
            base_branch="main",
            head_branch="dev",
            base_sha="base123",
            head_sha="head456",
            user="example",
            changed_files=1,
            additions=1,
            deletions=1,
        ),
        diff="+  z-index: 60;",
        diff_truncated=False,
    )


def make_finding(
    policy_sources: list[PolicySource],
    classification: str = "evidence_backed",
) -> LLMReviewFinding:
    return LLMReviewFinding(
        rule_id="LLM001",
        severity="medium",
        category="coding_standard",
        classification=classification,
        message="The changed value may bypass the documented layering token.",
        file_path="frontend/src/styles.css",
        line_number=10,
        evidence="+  z-index: 60;",
        evidence_explanation=(
            "The changed line sets a literal z-index value. "
            "Verify whether the project requires a shared layering token."
        ),
        policy_sources=policy_sources,
    )


def make_service(response: LLMReviewResult) -> LLMReviewService:
    service = LLMReviewService.__new__(LLMReviewService)
    service.model = FakeModel(response)
    return service


def test_accepts_citation_present_in_retrieved_evidence():
    evidence = [
        {
            "source": "css-layering-guidelines.md",
            "section": "CSS Layering Guidelines > Header",
            "content": "Use the documented layering token.",
            "similarity": 0.80,
        }
    ]

    response = LLMReviewResult(
        findings=[
            make_finding(
                [
                    PolicySource(
                        source="css-layering-guidelines.md",
                        section="CSS Layering Guidelines > Header",
                    )
                ]
            )
        ],
        summary="One finding requires verification.",
    )

    result = make_service(response).review(
        make_review_input(),
        policy_evidence=evidence,
    )

    assert len(result.findings) == 1
    assert result.findings[0].classification == "evidence_backed"


def test_rejects_citation_not_present_in_retrieved_evidence():
    evidence = [
        {
            "source": "css-layering-guidelines.md",
            "section": "CSS Layering Guidelines > Header",
            "content": "Use the documented layering token.",
            "similarity": 0.80,
        }
    ]

    response = LLMReviewResult(
        findings=[
            make_finding(
                [
                    PolicySource(
                        source="security.md",
                        section="Authentication",
                    )
                ]
            )
        ],
        summary="One finding.",
    )

    with pytest.raises(ValueError, match="not present in the retrieved evidence"):
        make_service(response).review(
            make_review_input(),
            policy_evidence=evidence,
        )


def test_accepts_uncertain_finding_without_policy_citation():
    response = LLMReviewResult(
        findings=[
            make_finding(
                policy_sources=[],
                classification="uncertain",
            )
        ],
        summary="One uncertain finding requires verification.",
    )

    result = make_service(response).review(
        make_review_input(),
        policy_evidence=[],
    )

    assert result.findings[0].classification == "uncertain"
    assert result.findings[0].policy_sources == []


def test_accepts_empty_findings():
    response = LLMReviewResult(
        findings=[],
        summary="No supported issues identified.",
    )

    result = make_service(response).review(
        make_review_input(),
        policy_evidence=[],
    )

    assert result.findings == []
