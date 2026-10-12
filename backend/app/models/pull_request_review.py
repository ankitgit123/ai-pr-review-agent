
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PullRequestReview(Base):
    __tablename__ = "pull_request_reviews"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    github_owner: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    repository_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    pull_request_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    pull_request_title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
