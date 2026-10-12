
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pull_request_review import PullRequestReview


def create_review(
    db: Session,
    review: PullRequestReview,
) -> PullRequestReview:
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_review_by_id(
    db: Session,
    review_id: str,
) -> PullRequestReview | None:
    statement = select(PullRequestReview).where(
        PullRequestReview.id == review_id
    )
    return db.execute(statement).scalar_one_or_none()


def list_reviews(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> list[PullRequestReview]:
    statement = (
        select(PullRequestReview)
        .order_by(PullRequestReview.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(statement).scalars().all())
