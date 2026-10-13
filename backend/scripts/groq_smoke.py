
from app.schemas.review_input import PullRequestData, ReviewInput
from app.services.llm_review_service import LLMReviewResult, LLMReviewService


def main() -> None:
    pull_request = PullRequestData(
        number=1,
        title="Synthetic null-safety test",
        state="open",
        draft=False,
        html_url="https://github.com/example/repo/pull/1",
        base_branch="main",
        head_branch="test",
        base_sha="base",
        head_sha="head",
        user="test-user",
        changed_files=1,
        additions=1,
        deletions=1,
    )

    diff = """diff --git a/app.js b/app.js
--- a/app.js
+++ b/app.js
@@ -1,2 +1,2 @@
-const name = user ? user.name : "Guest";
+const name = user.name.trim();
"""

    review_input = ReviewInput(
        pull_request=pull_request,
        diff=diff,
        diff_truncated=False,
    )

    result = LLMReviewService().review(
        review_input,
        policy_evidence=[],
    )

    print("Structured result:", isinstance(result, LLMReviewResult))
    print("Findings:", len(result.findings))
    print("Summary:", result.summary)

    for finding in result.findings:
        print({
            "rule_id": finding.rule_id,
            "severity": finding.severity,
            "classification": finding.classification,
            "file_path": finding.file_path,
            "line_number": finding.line_number,
            "evidence": finding.evidence,
            "policy_sources": [
                source.model_dump()
                for source in finding.policy_sources
            ],
        })


if __name__ == "__main__":
    main()
