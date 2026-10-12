
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PullRequestReviewCreate(BaseModel):
    github_owner: str = Field(min_length=1, max_length=100)
    repository_name: str = Field(min_length=1, max_length=100)
    pull_request_number: int = Field(gt=0)
    pull_request_title: str | None = Field(default=None, max_length=500)


class PullRequestReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    github_owner: str
    repository_name: str
    pull_request_number: int
    pull_request_title: str | None
    status: Literal["pending", "in_progress", "completed", "failed"]
    created_at: datetime
