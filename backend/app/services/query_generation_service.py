    
import re


class QueryGenerationService:
    """Generate deterministic knowledge-retrieval queries from a PR diff."""

    MAX_QUERIES = 3

    FILE_PATTERN = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)
    ADDED_LINE_PATTERN = re.compile(r"^\+(?!\+\+)(.*)$", re.MULTILINE)

    def generate_queries(self, diff: str) -> list[str]:
        """Create focused queries from changed files and added code."""

        if not diff or not diff.strip():
            return []

        file_paths = sorted(set(self.FILE_PATTERN.findall(diff)))
        added_lines = self.ADDED_LINE_PATTERN.findall(diff)
        added_code = "\n".join(added_lines).lower()

        queries: list[str] = []

        # Query 1: General conventions relevant to changed files.
        if file_paths:
            paths = ", ".join(file_paths[:5])
            queries.append(
                "What coding standards, project conventions, and "
                f"best practices apply to changes in these files: {paths}?"
            )

        # Query 2: CSS layering rules when stacking behavior changes.
        if (
            any(path.lower().endswith(".css") for path in file_paths)
            and "z-index" in added_code
        ):
            queries.append(
                "What coding standards govern z-index values, header "
                "layering, shared layering tokens, and stacking order?"
            )

        # Query 3: Security guidance when code changes involve credentials
        # or common security-sensitive operations.
        security_terms = (
            "password",
            "secret",
            "token",
            "authorization",
            "subprocess",
            "eval(",
        )

        if any(term in added_code for term in security_terms):
            queries.append(
                "What security standards apply to the changed code, "
                "including secrets, authorization, and unsafe operations?"
            )

        # Ensure a useful query exists even when the diff has no recognized
        # file path or special concept.
        if not queries:
            queries.append(
                "What coding standards and project conventions are relevant "
                "to the changes in this pull request?"
            )

        # Remove duplicates while preserving order.
        return list(dict.fromkeys(queries))[: self.MAX_QUERIES]
