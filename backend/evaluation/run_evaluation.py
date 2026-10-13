
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.review_input import PullRequestData, ReviewInput
from app.services.deterministic_review_service import (
    DeterministicReviewService,
)
from app.services.finding_validation_service import (
    FindingValidationService,
)
from app.services.llm_review_service import LLMReviewService
from app.services.retrieval_service import RetrievalService


EVALUATION_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = EVALUATION_DIR / "manifest.json"
REPORTS_DIR = EVALUATION_DIR / "reports"


def load_manifest() -> dict[str, Any]:
    """Load and minimally validate the evaluation manifest."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    if not isinstance(manifest.get("cases"), list) or not manifest["cases"]:
        raise ValueError("Evaluation manifest must contain a non-empty cases list.")

    case_ids = [case.get("id") for case in manifest["cases"]]
    if any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
        raise ValueError("Every evaluation case must have a non-empty id.")

    if len(case_ids) != len(set(case_ids)):
        raise ValueError("Evaluation case IDs must be unique.")

    return manifest


def build_review_input(case: dict[str, Any], diff: str) -> ReviewInput:
    """Build synthetic PR metadata; never contacts GitHub."""
    case_id = case["id"]

    pull_request = PullRequestData(
        number=1,
        title=f"Evaluation case: {case_id}",
        state="open",
        draft=False,
        html_url=f"https://github.com/evaluation-fixtures/{case_id}/pull/1",
        base_branch="main",
        head_branch=f"evaluation/{case_id}",
        base_sha="synthetic-base",
        head_sha="synthetic-head",
        user="evaluation-runner",
        changed_files=1,
        additions=len(case["expected_added_lines"]),
        deletions=0,
    )

    return ReviewInput(
        pull_request=pull_request,
        diff=diff,
        diff_truncated=False,
    )


def run_case(
    case: dict[str, Any],
    deterministic_service: DeterministicReviewService,
    retrieval_service: RetrievalService,
    llm_service: LLMReviewService,
    validation_service: FindingValidationService,
) -> dict[str, Any]:
    """Run one fixture and capture failures without hiding them."""
    started = time.perf_counter()
    case_id = case["id"]

    result: dict[str, Any] = {
        "case_id": case_id,
        "expected": case["expected"],
        "source": "synthetic",
        "status": "failed",
        "duration_seconds": None,
        "deterministic_review": None,
        "policy_evidence": None,
        "llm_review": None,
        "finding_validations": None,
        "error": None,
    }

    try:
        fixture_path = (EVALUATION_DIR / case["fixture"]).resolve()

        if not fixture_path.is_relative_to(EVALUATION_DIR.resolve()):
            raise ValueError("Fixture path must remain inside the evaluation directory.")

        if not fixture_path.is_file():
            raise FileNotFoundError(f"Fixture not found: {case['fixture']}")

        diff = fixture_path.read_text(encoding="utf-8")

        if not diff.strip():
            raise ValueError("Evaluation fixture is empty.")

        review_input = build_review_input(case, diff)

        deterministic = deterministic_service.review(diff)
        policy_evidence = retrieval_service.retrieve(
            diff=diff,
            top_k_per_query=3,
            max_results=5,
        )
        llm_result = llm_service.review(
            review_input,
            policy_evidence=policy_evidence,
        )

        validations = []
        for index, finding in enumerate(llm_result.findings):
            validation = validation_service.validate(
                finding=finding,
                diff=diff,
            )
            validations.append(
                {
                    "finding_index": index,
                    "rule_id": finding.rule_id,
                    "file_path": finding.file_path,
                    "line_number": finding.line_number,
                    "valid": validation.valid,
                    "errors": list(validation.errors),
                }
            )

        result.update(
            {
                "status": "completed",
                "deterministic_review": deterministic.model_dump(mode="json"),
                "policy_evidence": policy_evidence,
                "llm_review": llm_result.model_dump(mode="json"),
                "finding_validations": validations,
            }
        )

    except Exception as exc:
        # Record the exception type and message, not credentials or request headers.
        result["error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }

    finally:
        result["duration_seconds"] = round(
            time.perf_counter() - started,
            3,
        )

    return result


def main() -> int:
    manifest = load_manifest()

    # Construct shared services once, rather than reloading models per case.
    deterministic_service = DeterministicReviewService()
    retrieval_service = RetrievalService()
    llm_service = LLMReviewService()
    validation_service = FindingValidationService()

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for case in manifest["cases"]:
        print(f"Running evaluation case: {case['id']}")

        result = run_case(
            case,
            deterministic_service,
            retrieval_service,
            llm_service,
            validation_service,
        )
        results.append(result)

        print(
            f"  Status: {result['status']} | "
            f"Duration: {result['duration_seconds']}s"
        )
        if result["error"]:
            print(
                f"  Error: {result['error']['type']}: "
                f"{result['error']['message']}"
            )

    completed = sum(item["status"] == "completed" for item in results)
    failed = len(results) - completed

    report = {
        "dataset_version": manifest["dataset_version"],
        "description": manifest["description"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        "case_count": len(results),
        "completed_count": completed,
        "failed_count": failed,
        "results": results,
        "interpretation_note": (
            "Completed means the pipeline executed, not that the model was correct. "
            "Expected labels are not yet a human-verified benchmark."
        ),
    }

    report_path = REPORTS_DIR / (
        f"evaluation-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    )
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print(f"Completed: {completed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")
    print(f"Report: {report_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
