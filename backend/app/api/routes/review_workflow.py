
import logging

from fastapi import APIRouter, HTTPException, Path
from groq import APIConnectionError, APIStatusError, AuthenticationError, RateLimitError

from app.integrations.github.client import GitHubClientError
from app.services.pull_request_review_workflow import (
    PullRequestReviewWorkflow,
)

logger = logging.getLogger(__name__)

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

    try:
        workflow = PullRequestReviewWorkflow()
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

    except AuthenticationError:
        logger.exception("AI provider authentication failed")
        raise HTTPException(
            status_code=502,
            detail="AI review provider authentication failed.",
        ) from None

    except RateLimitError:
        logger.exception("AI provider rate limit reached")
        raise HTTPException(
            status_code=503,
            detail="AI review provider rate limit reached. Please try again later.",
        ) from None

    except (APIConnectionError, APIStatusError):
        logger.exception("AI provider request failed")
        raise HTTPException(
            status_code=502,
            detail="AI review provider request failed.",
        ) from None

    except Exception:
        logger.exception("Unexpected pull-request review failure")
        raise HTTPException(
            status_code=500,
            detail="The review could not be completed.",
        ) from None
