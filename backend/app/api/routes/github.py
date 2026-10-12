
from fastapi import APIRouter, HTTPException, Path

from app.integrations.github.client import (
    GitHubClient,
    GitHubClientError,
)

router = APIRouter(prefix="/api/github", tags=["GitHub"])

MAX_DIFF_CHARACTERS = 100_000


@router.get("/pull-requests/{owner}/{repository}/{pull_request_number}")
def fetch_pull_request(
    owner: str = Path(min_length=1, max_length=100),
    repository: str = Path(min_length=1, max_length=100),
    pull_request_number: int = Path(gt=0),
) -> dict:
    """Fetch pull-request metadata and its code diff from GitHub."""

    client = GitHubClient()

    try:
        pull_request = client.get_pull_request(
            owner=owner,
            repository=repository,
            pull_request_number=pull_request_number,
        )

        diff = client.get_pull_request_diff(
            owner=owner,
            repository=repository,
            pull_request_number=pull_request_number,
        )

        truncated = len(diff) > MAX_DIFF_CHARACTERS
        if truncated:
            diff = diff[:MAX_DIFF_CHARACTERS]

        return {
            "pull_request": pull_request,
            "diff": diff,
            "diff_truncated": truncated,
        }

    except GitHubClientError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from None
