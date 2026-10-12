
import os
import re

import httpx


GITHUB_API_BASE_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"


class GitHubClientError(Exception):
    """Safe, user-facing error raised by the GitHub integration."""


class GitHubClient:
    """Read-only client for fetching GitHub pull-request data."""

    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

    def _get_headers(self, accept: str) -> dict[str, str]:
        headers = {
            "Accept": accept,
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    @staticmethod
    def _validate_repository(
        owner: str,
        repository: str,
        pull_request_number: int,
    ) -> None:
        # Restrict path segments to prevent arbitrary URL/path injection.
        segment_pattern = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")

        if (
            not segment_pattern.fullmatch(owner)
            or owner in {".", ".."}
            or not segment_pattern.fullmatch(repository)
            or repository in {".", ".."}
        ):
            raise GitHubClientError(
                "Invalid GitHub owner or repository name."
            )

        if pull_request_number <= 0:
            raise GitHubClientError(
                "Pull request number must be a positive integer."
            )

    def _get(
        self,
        url: str,
        accept: str,
    ) -> httpx.Response:
        try:
            response = httpx.get(
                url,
                headers=self._get_headers(accept),
                timeout=20.0,
                follow_redirects=False,
            )
        except httpx.TimeoutException:
            raise GitHubClientError(
                "GitHub request timed out. Please try again."
            ) from None
        except httpx.RequestError:
            raise GitHubClientError(
                "Could not connect to GitHub."
            ) from None

        if response.status_code == 404:
            raise GitHubClientError(
                "Pull request or repository not found, or access is denied."
            )

        if response.status_code == 401:
            raise GitHubClientError(
                "GitHub authentication failed. Check the configured token."
            )

        if response.status_code == 403:
            raise GitHubClientError(
                "GitHub denied the request. Check token permissions or rate limits."
            )

        if response.status_code == 429:
            raise GitHubClientError(
                "GitHub rate limit reached. Please try again later."
            )

        if response.is_error:
            raise GitHubClientError(
                f"GitHub returned HTTP {response.status_code}."
            )

        return response

    def get_pull_request(
        self,
        owner: str,
        repository: str,
        pull_request_number: int,
    ) -> dict:
        """Fetch selected metadata for a pull request."""

        self._validate_repository(
            owner, repository, pull_request_number
        )

        url = (
            f"{GITHUB_API_BASE_URL}/repos/"
            f"{owner}/{repository}/pulls/{pull_request_number}"
        )

        response = self._get(
            url,
            accept="application/vnd.github+json",
        )

        data = response.json()

        # Return only fields needed by our application.
        return {
            "number": data["number"],
            "title": data["title"],
            "state": data["state"],
            "draft": data["draft"],
            "html_url": data["html_url"],
            "base_branch": data["base"]["ref"],
            "head_branch": data["head"]["ref"],
            "base_sha": data["base"]["sha"],
            "head_sha": data["head"]["sha"],
            "user": data["user"]["login"],
            "changed_files": data["changed_files"],
            "additions": data["additions"],
            "deletions": data["deletions"],
        }

    def get_pull_request_diff(
        self,
        owner: str,
        repository: str,
        pull_request_number: int,
    ) -> str:
        """Fetch the text diff for a pull request."""

        self._validate_repository(
            owner, repository, pull_request_number
        )

        url = (
            f"{GITHUB_API_BASE_URL}/repos/"
            f"{owner}/{repository}/pulls/{pull_request_number}"
        )

        response = self._get(
            url,
            accept="application/vnd.github.diff",
        )

        return response.text
