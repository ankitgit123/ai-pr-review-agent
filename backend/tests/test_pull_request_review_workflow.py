
from unittest.mock import Mock, call

import pytest

from app.integrations.github.client import GitHubClient
from app.schemas.review_input import PullRequestData
from app.services.deterministic_review_service import (
    DeterministicReviewResult,
)
from app.services.llm_review_service import (
    LLMReviewResult,
)
from app.services.pull_request_review_workflow import (
    PullRequestReviewWorkflow,
)


@pytest.fixture
def workflow():
    """Create the workflow with mocked dependencies."""

    instance = PullRequestReviewWorkflow.__new__(
        PullRequestReviewWorkflow
    )

    # The spec prevents accidentally relying on nonexistent GitHub methods.
    instance.github_client = Mock(spec=GitHubClient)
    instance.deterministic_review_service = Mock()
    instance.retrieval_service = Mock()
    instance.llm_review_service = Mock()

    instance.github_client.get_pull_request.return_value = (
        PullRequestData(
            number=1,
            title="Increase z-index of header from 50 to 60",
            state="open",
            draft=False,
            html_url="https://github.com/example/repo/pull/1",
            base_branch="main",
            head_branch="dev",
            base_sha="base-sha",
            head_sha="head-sha",
            user="example",
            changed_files=1,
            additions=2,
            deletions=2,
        )
    )

    instance.github_client.get_pull_request_diff.return_value = (
        "diff --git a/frontend/src/styles.css "
        "b/frontend/src/styles.css\n"
        "@@ -60,1 +60,1 @@\n"
        "-  z-index: 50;\n"
        "+  z-index: 60;\n"
    )

    instance.deterministic_review_service.review.return_value = (
        DeterministicReviewResult(
            engine="deterministic",
            files_changed=["frontend/src/styles.css"],
            findings=[],
            summary="No deterministic findings.",
        )
    )

    instance.retrieval_service.retrieve.return_value = [
        {
            "chunk_id": "header-guideline-1",
            "source": "css-layering-guidelines.md",
            "section": "CSS Layering Guidelines > Header",
            "content": (
                "The header should use the project's documented "
                "layering token."
            ),
            "similarity": 0.80,
            "matched_queries": ["CSS layering conventions"],
        }
    ]

    instance.llm_review_service.review.return_value = (
        LLMReviewResult(
            findings=[],
            summary="No confirmed issues identified.",
        )
    )

    return instance


def test_passes_same_diff_to_deterministic_review_and_retrieval(
    workflow,
):
    """Both services must receive the diff fetched from GitHub."""

    workflow.run("example", "repo", 1)

    diff = workflow.github_client.get_pull_request_diff.return_value

    workflow.deterministic_review_service.review.assert_called_once_with(
        diff
    )
    workflow.retrieval_service.retrieve.assert_called_once_with(
        diff=diff,
        top_k_per_query=3,
        max_results=5,
    )


def test_passes_retrieved_policy_evidence_to_llm(workflow):
    """The LLM must receive the evidence returned by retrieval."""

    workflow.run("example", "repo", 1)

    workflow.llm_review_service.review.assert_called_once()

    review_input = (
        workflow.llm_review_service.review.call_args.args[0]
    )
    kwargs = workflow.llm_review_service.review.call_args.kwargs

    assert review_input.diff == (
        workflow.github_client.get_pull_request_diff.return_value
    )
    assert kwargs["policy_evidence"] == (
        workflow.retrieval_service.retrieve.return_value
    )


def test_returns_all_review_results_and_policy_evidence(workflow):
    """The combined result must preserve every service's output."""

    result = workflow.run("example", "repo", 1)

    assert result.pull_request.number == 1
    assert result.deterministic_review is (
        workflow.deterministic_review_service.review.return_value
    )
    assert result.llm_review is (
        workflow.llm_review_service.review.return_value
    )
    assert result.policy_evidence == (
        workflow.retrieval_service.retrieve.return_value
    )
    assert result.diff_truncated is False


def test_propagates_invalid_policy_citation_error(workflow):
    """A citation-validation failure must not be silently ignored."""

    workflow.llm_review_service.review.side_effect = ValueError(
        "The model returned a policy citation that was not "
        "present in the retrieved evidence."
    )

    with pytest.raises(
        ValueError,
        match="policy citation",
    ):
        workflow.run("example", "repo", 1)


def test_github_integration_uses_only_read_operations(workflow):
    """The workflow must fetch PR data without attempting GitHub writes."""

    workflow.run("example", "repo", 1)

    assert workflow.github_client.method_calls == [
        call.get_pull_request(
            owner="example",
            repository="repo",
            pull_request_number=1,
        ),
        call.get_pull_request_diff(
            owner="example",
            repository="repo",
            pull_request_number=1,
        ),
    ]


def test_empty_policy_evidence_is_passed_to_llm(workflow):
    """No retrieval results must remain an explicit empty evidence list."""

    workflow.retrieval_service.retrieve.return_value = []

    workflow.run("example", "repo", 1)

    kwargs = workflow.llm_review_service.review.call_args.kwargs
    assert kwargs["policy_evidence"] == []


def test_invalid_llm_finding_is_reported_in_validation_results(workflow):
    """An unsupported finding must be marked invalid, not silently trusted."""

    from app.services.llm_review_service import LLMReviewFinding
    from app.services.finding_validation_service import (
        FindingValidationResult,
    )

    finding = LLMReviewFinding(
        rule_id="TEST001",
        severity="high",
        category="security",
        message="Potential authorization issue.",
        file_path="frontend/src/other.py",
        line_number=99,
        evidence="unauthorized_access()",
        evidence_explanation="The access check may be missing.",
        policy_sources=[],
        classification="uncertain",
    )

    workflow.llm_review_service.review.return_value = LLMReviewResult(
        findings=[finding],
        summary="One finding requires verification.",
    )

    workflow.finding_validation_service = Mock()
    workflow.finding_validation_service.validate.return_value = (
        FindingValidationResult(
            valid=False,
            errors=("File is not part of the diff.",),
        )
    )

    result = workflow.run("example", "repo", 1)

    assert len(result.finding_validations) == 1
    assert result.finding_validations[0].valid is False
    assert "File is not part of the diff." in (
        result.finding_validations[0].errors
    )

    # The model output is preserved separately from validation status.
    assert result.llm_review.findings == [finding]
    assert result.finding_validations[0].valid is False
    assert result.finding_validations[0].errors

