
import httpx
import pytest
from unittest.mock import patch

from app.integrations.github.client import GitHubClient, GitHubClientError


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("GITHUB_PERSONAL_ACCESS_TOKEN", raising=False)
    return GitHubClient()


def make_pr_response():
    return {
        "number": 1,
        "title": "Increase header z-index",
        "state": "open",
        "draft": False,
        "html_url": "https://github.com/example/repo/pull/1",
        "base": {"ref": "main", "sha": "base-sha"},
        "head": {"ref": "feature", "sha": "head-sha"},
        "user": {"login": "developer"},
        "changed_files": 1,
        "additions": 2,
        "deletions": 1,
    }



def make_response(status_code, *, json_data=None, text=""):
    request = httpx.Request(
        "GET", "https://api.github.com/repos/example/repo/pulls/1"
    )

    if json_data is not None:
        return httpx.Response(
            status_code,
            json=json_data,
            request=request,
        )

    return httpx.Response(
        status_code,
        text=text,
        request=request,
    )



def test_get_pull_request_returns_selected_metadata(client):
    response = make_response(200, json_data=make_pr_response())

    with patch(
        "app.integrations.github.client.httpx.get",
        return_value=response,
    ) as mocked_get:
        result = client.get_pull_request("example", "repo", 1)

    assert result["number"] == 1
    assert result["title"] == "Increase header z-index"
    assert result["base_branch"] == "main"
    assert result["head_branch"] == "feature"
    assert result["user"] == "developer"
    assert result["changed_files"] == 1

    headers = mocked_get.call_args.kwargs["headers"]
    assert "Authorization" not in headers
    assert headers["Accept"] == "application/vnd.github+json"


def test_get_pull_request_diff_returns_text(client):
    diff = "diff --git a/app.py b/app.py\n+print('hello')\n"

    with patch(
        "app.integrations.github.client.httpx.get",
        return_value=make_response(200, text=diff),
    ) as mocked_get:
        result = client.get_pull_request_diff("example", "repo", 1)

    assert result == diff
    assert (
        mocked_get.call_args.kwargs["headers"]["Accept"]
        == "application/vnd.github.diff"
    )


@pytest.mark.parametrize(
    ("owner", "repository", "number", "message"),
    [
        ("example", "repo", 0, "positive integer"),
        ("example", "repo", -1, "positive integer"),
        ("owner/name", "repo", 1, "Invalid GitHub owner"),
        ("example", "../repo", 1, "Invalid GitHub owner"),
    ],
)
def test_invalid_input_is_rejected_before_http_request(
    client, owner, repository, number, message
):
    with patch("app.integrations.github.client.httpx.get") as mocked_get:
        with pytest.raises(GitHubClientError, match=message):
            client.get_pull_request(owner, repository, number)

    mocked_get.assert_not_called()


@pytest.mark.parametrize(
    ("status_code", "message"),
    [
        (401, "authentication failed"),
        (403, "denied the request"),
        (404, "not found"),
        (429, "rate limit"),
        (500, "HTTP 500"),
    ],
)
def test_http_errors_are_mapped_to_client_errors(
    client, status_code, message
):
    with patch(
        "app.integrations.github.client.httpx.get",
        return_value=make_response(status_code),
    ):
        with pytest.raises(GitHubClientError, match=message):
            client.get_pull_request("example", "repo", 1)


@pytest.mark.parametrize(
    ("exception", "message"),
    [
        (httpx.TimeoutException("timeout"), "timed out"),
        (httpx.ConnectError("connection failed"), "Could not connect"),
    ],
)
def test_network_errors_are_mapped_to_client_errors(
    client, exception, message
):
    with patch(
        "app.integrations.github.client.httpx.get",
        side_effect=exception,
    ):
        with pytest.raises(GitHubClientError, match=message):
            client.get_pull_request("example", "repo", 1)


def test_token_is_sent_when_configured(monkeypatch):
    monkeypatch.setenv("GITHUB_PERSONAL_ACCESS_TOKEN", "test-token")
    client = GitHubClient()

    with patch(
        "app.integrations.github.client.httpx.get",
        return_value=make_response(200, json_data=make_pr_response()),
    ) as mocked_get:
        client.get_pull_request("example", "repo", 1)

    assert (
        mocked_get.call_args.kwargs["headers"]["Authorization"]
        == "Bearer test-token"
    )
