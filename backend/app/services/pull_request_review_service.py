
from sqlalchemy.orm import Session

from app.models.pull_request_review import PullRequestReview
from app.repositories.pull_request_review_repository import (
    create_review as repository_create_review,
    get_review_by_id as repository_get_review_by_id,
    list_reviews as repository_list_reviews,
)
from app.schemas.pull_request_review import PullRequestReviewCreate


def create_review(
    db: Session,
    payload: PullRequestReviewCreate,
) -> PullRequestReview:
    review = PullRequestReview(
        github_owner=payload.github_owner,
        repository_name=payload.repository_name,
        pull_request_number=payload.pull_request_number,
        pull_request_title=payload.pull_request_title,
        status="pending",
    )

    return repository_create_review(db, review)


def get_review_by_id(
    db: Session,
    review_id: str,
) -> PullRequestReview | None:
    return repository_get_review_by_id(db, review_id)


def list_reviews(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> list[PullRequestReview]:
    return repository_list_reviews(
        db,
        limit=limit,
        offset=offset,
    )
