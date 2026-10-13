
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.integrations.github.client import GitHubClientError
from app.main import app


client = TestClient(app)


def test_fetch_pull_request_returns_metadata_and_diff():
    metadata = {
        "number": 1,
        "title": "Example PR",
        "state": "open",
        "draft": False,
        "html_url": "https://github.com/example/repo/pull/1",
        "base_branch": "main",
        "head_branch": "feature",
        "base_sha": "base",
        "head_sha": "head",
        "user": "developer",
        "changed_files": 1,
        "additions": 1,
        "deletions": 0,
    }

    with (
        patch("app.api.routes.github.GitHubClient") as mock_client_class,
    ):
        mock_client = mock_client_class.return_value
        mock_client.get_pull_request.return_value = metadata
        mock_client.get_pull_request_diff.return_value = "+print('hello')"

        response = client.get(
            "/api/github/pull-requests/example/repo/1"
        )

    assert response.status_code == 200
    assert response.json()["pull_request"] == metadata
    assert response.json()["diff"] == "+print('hello')"
    assert response.json()["diff_truncated"] is False


def test_fetch_pull_request_maps_client_error_to_502():
    with patch("app.api.routes.github.GitHubClient") as mock_client_class:
        mock_client_class.return_value.get_pull_request.side_effect = (
            GitHubClientError("GitHub request timed out. Please try again.")
        )

        response = client.get(
            "/api/github/pull-requests/example/repo/1"
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "GitHub request timed out. Please try again."
    )


def test_invalid_pull_request_number_is_rejected_by_api():
    with patch("app.api.routes.github.GitHubClient") as mock_client_class:
        response = client.get(
            "/api/github/pull-requests/example/repo/0"
        )

    assert response.status_code == 422
    mock_client_class.assert_not_called()


def test_large_diff_is_truncated():
    metadata = {
        "number": 1,
        "title": "Example PR",
        "state": "open",
        "draft": False,
        "html_url": "https://github.com/example/repo/pull/1",
        "base_branch": "main",
        "head_branch": "feature",
        "base_sha": "base",
        "head_sha": "head",
        "user": "developer",
        "changed_files": 1,
        "additions": 1,
        "deletions": 0,
    }

    large_diff = "x" * 100_001

    with patch("app.api.routes.github.GitHubClient") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.get_pull_request.return_value = metadata
        mock_client.get_pull_request_diff.return_value = large_diff

        response = client.get(
            "/api/github/pull-requests/example/repo/1"
        )

    assert response.status_code == 200
    assert len(response.json()["diff"]) == 100_000
    assert response.json()["diff_truncated"] is True
