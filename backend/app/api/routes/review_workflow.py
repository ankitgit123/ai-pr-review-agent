
from fastapi import APIRouter, HTTPException, Path

from app.integrations.github.client import GitHubClientError
from app.services.pull_request_review_workflow import (
    PullRequestReviewWorkflow,
)

router = APIRouter(
    prefix="/api/review-workflow",
    tags=["Review Workflow"],
)


@router.post("/{owner}/{repository}/{pull_request_number}")
def review_pull_request(
    owner: str = Path(min_length=1, max_length=100),
    repository: str = Path(min_length=1, max_length=100),
    pull_request_number: int = Path(gt=0),
) -> dict:
    """Fetch a GitHub PR and run the deterministic review workflow."""

    workflow = PullRequestReviewWorkflow()

    try:
        result = workflow.run(
            owner=owner,
            repository=repository,
            pull_request_number=pull_request_number,
        )
        return result.model_dump(mode="json")

    except GitHubClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from None
