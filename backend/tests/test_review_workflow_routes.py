
from unittest.mock import patch

from fastapi.testclient import TestClient
from groq import AuthenticationError

from app.integrations.github.client import GitHubClientError
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_review_workflow_maps_github_error_to_502():
    with patch(
        "app.api.routes.review_workflow.PullRequestReviewWorkflow"
    ) as workflow_class:
        workflow_class.return_value.run.side_effect = GitHubClientError(
            "Pull request or repository not found."
        )

        response = client.post(
            "/api/review-workflow/example/repo/1"
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Pull request or repository not found."
    )


def test_review_workflow_handles_groq_authentication_error():
    with patch(
        "app.api.routes.review_workflow.PullRequestReviewWorkflow"
    ) as workflow_class:
        workflow_class.return_value.run.side_effect = AuthenticationError(
            "Invalid API Key",
            response=__import__("httpx").Response(
                401,
                request=__import__("httpx").Request(
                    "POST", "https://api.groq.com/openai/v1/chat/completions"
                ),
            ),
            body={
                "error": {
                    "message": "Invalid API Key",
                    "code": "invalid_api_key",
                }
            },
        )

        response = client.post(
            "/api/review-workflow/example/repo/1"
        )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "AI review provider authentication failed."
    )
    assert "Invalid API Key" not in response.text


def test_review_workflow_hides_unexpected_exception_details():
    with patch(
        "app.api.routes.review_workflow.PullRequestReviewWorkflow"
    ) as workflow_class:
        workflow_class.return_value.run.side_effect = RuntimeError(
            "internal details must not reach the client"
        )

        response = client.post(
            "/api/review-workflow/example/repo/1"
        )

    assert response.status_code == 500
    assert response.json()["detail"] == (
        "The review could not be completed."
    )
    assert "internal details" not in response.text


def test_invalid_pull_request_number_is_rejected():
    with patch(
        "app.api.routes.review_workflow.PullRequestReviewWorkflow"
    ) as workflow_class:
        response = client.post(
            "/api/review-workflow/example/repo/0"
        )

    assert response.status_code == 422
    workflow_class.assert_not_called()
