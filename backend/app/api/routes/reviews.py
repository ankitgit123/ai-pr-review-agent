
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.pull_request_review import (
    PullRequestReviewCreate,
    PullRequestReviewResponse,
)
from app.services.pull_request_review_service import (
    create_review,
    get_review_by_id,
    list_reviews,
)

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


@router.post(
    "",
    response_model=PullRequestReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_pull_request_review(
    payload: PullRequestReviewCreate,
    db: Session = Depends(get_db),
):
    return create_review(db, payload)


@router.get(
    "",
    response_model=list[PullRequestReviewResponse],
)
def list_pull_request_reviews(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return list_reviews(db, limit=limit, offset=offset)


@router.get(
    "/{review_id}",
    response_model=PullRequestReviewResponse,
)
def read_pull_request_review(
    review_id: str,
    db: Session = Depends(get_db),
):
    review = get_review_by_id(db, review_id)

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    return review
