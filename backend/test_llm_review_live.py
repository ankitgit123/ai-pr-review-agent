
from app.integrations.github.client import GitHubClient
from app.schemas.review_input import ReviewInput
from app.services.llm_review_service import LLMReviewService


def main() -> None:
    owner = "ankitgit123"
    repository = "book-worm"
    pull_request_number = 1

    # 1. Fetch the real PR metadata and diff from GitHub.
    github = GitHubClient()

    pull_request = github.get_pull_request(
        owner=owner,
        repository=repository,
        pull_request_number=pull_request_number,
    )

    diff = github.get_pull_request_diff(
        owner=owner,
        repository=repository,
        pull_request_number=pull_request_number,
    )

    # 2. Apply the same diff-size limit as the review workflow.
    max_diff_characters = 100_000
    diff_truncated = len(diff) > max_diff_characters

    if diff_truncated:
        diff = diff[:max_diff_characters]

    # 3. Validate the data before sending it to the model.
    review_input = ReviewInput.model_validate(
        {
            "pull_request": pull_request,
            "diff": diff,
            "diff_truncated": diff_truncated,
        }
    )

    print("GitHub fetch and input validation succeeded.")
    print(f"PR: #{review_input.pull_request.number}")
    print(f"Title: {review_input.pull_request.title}")
    print(f"Diff characters: {len(review_input.diff)}")
    print("Calling Groq LLM...")

    # 4. Run the LLM review directly, without FastAPI.
    service = LLMReviewService()
    result = service.review(review_input)

    # 5. Print the structured result, not credentials.
    print("\nStructured LLM review result:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
