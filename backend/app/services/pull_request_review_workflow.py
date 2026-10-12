
from pydantic import BaseModel, ConfigDict

from app.integrations.github.client import GitHubClient
from app.schemas.review_input import PullRequestData, ReviewInput
from app.services.deterministic_review_service import (
    DeterministicReviewService,
    DeterministicReviewResult,
)
from app.services.finding_validation_service import (
    FindingValidationService,
)
from app.services.llm_review_service import LLMReviewService, LLMReviewResult
from app.services.retrieval_service import RetrievalService


class FindingValidationReport(BaseModel):
    """Application validation result for one LLM finding."""

    model_config = ConfigDict(extra="forbid")

    finding_index: int
    rule_id: str
    file_path: str
    line_number: int
    valid: bool
    errors: list[str]


class PullRequestWorkflowResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pull_request: PullRequestData
    deterministic_review: DeterministicReviewResult
    llm_review: LLMReviewResult
    policy_evidence: list[dict]
    finding_validations: list[FindingValidationReport]
    diff_truncated: bool


class PullRequestReviewWorkflow:
    def __init__(self):
        self.github_client = GitHubClient()
        self.deterministic_review_service = DeterministicReviewService()
        self.retrieval_service = RetrievalService()
        self.llm_review_service = LLMReviewService()
        self.finding_validation_service = FindingValidationService()

    def run(
        self,
        owner: str,
        repository: str,
        pull_request_number: int,
    ) -> PullRequestWorkflowResult:
        # 1. Fetch PR metadata and diff using read-only GitHub requests.
        pull_request = self.github_client.get_pull_request(
            owner=owner,
            repository=repository,
            pull_request_number=pull_request_number,
        )

        diff = self.github_client.get_pull_request_diff(
            owner=owner,
            repository=repository,
            pull_request_number=pull_request_number,
        )

        diff_truncated = len(diff) > 100_000
        if diff_truncated:
            diff = diff[:100_000]

        review_input = ReviewInput(
            pull_request=pull_request,
            diff=diff,
            diff_truncated=diff_truncated,
        )

        # 2. Run existing deterministic checks.
        deterministic_result = self.deterministic_review_service.review(
            review_input.diff
        )

        # 3. Retrieve relevant coding-standard evidence.
        policy_evidence = self.retrieval_service.retrieve(
            diff=review_input.diff,
            top_k_per_query=3,
            max_results=5,
        )

        # 4. Review the diff with retrieved policy evidence.
        llm_result = self.llm_review_service.review(
            review_input,
            policy_evidence=policy_evidence,
        )

        # 5. Independently validate every LLM finding against the diff.
        finding_validations = []

        for index, finding in enumerate(llm_result.findings):
            validation = self.finding_validation_service.validate(
                finding=finding,
                diff=review_input.diff,
            )

            finding_validations.append(
                FindingValidationReport(
                    finding_index=index,
                    rule_id=finding.rule_id,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                    valid=validation.valid,
                    errors=list(validation.errors),
                )
            )

        # 6. Preserve original findings and return validation separately.
        return PullRequestWorkflowResult(
            pull_request=review_input.pull_request,
            deterministic_review=deterministic_result,
            llm_review=llm_result,
            policy_evidence=policy_evidence,
            finding_validations=finding_validations,
            diff_truncated=review_input.diff_truncated,
        )
