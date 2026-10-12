
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class PullRequestData(BaseModel):
    """Selected metadata fetched from GitHub."""

    model_config = ConfigDict(extra="forbid")

    number: int = Field(gt=0)
    title: str
    state: str
    draft: bool
    html_url: HttpUrl
    base_branch: str
    head_branch: str
    base_sha: str
    head_sha: str
    user: str
    changed_files: int = Field(ge=0)
    additions: int = Field(ge=0)
    deletions: int = Field(ge=0)


class ReviewInput(BaseModel):
    """Validated input passed into the PR review workflow."""

    model_config = ConfigDict(extra="forbid")

    pull_request: PullRequestData
    diff: str
    diff_truncated: bool
