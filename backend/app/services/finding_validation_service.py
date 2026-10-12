
import re
from dataclasses import dataclass

from app.services.llm_review_service import LLMReviewFinding


@dataclass(frozen=True)
class FindingValidationResult:
    """Validation outcome for a single LLM-generated finding."""

    valid: bool
    errors: tuple[str, ...]


class FindingValidationService:
    """Validate a finding's file, added-line evidence, and new-file line."""

    HUNK_HEADER_PATTERN = re.compile(
        r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@"
    )
    FILE_HEADER_PATTERN = re.compile(r"^\+\+\+ b/(.+)$")

    @staticmethod
    def _normalize_evidence(evidence: str) -> str:
        """Remove one optional diff '+' marker and surrounding whitespace."""

        normalized = evidence.strip()

        # LLM output sometimes includes the diff marker in its quotation.
        # Remove exactly one leading '+'; do not alter the code itself.
        if normalized.startswith("+"):
            normalized = normalized[1:]

        return normalized.strip()

    def _extract_added_lines(
        self,
        diff: str,
    ) -> tuple[dict[str, dict[int, str]], set[str]]:
        """Map each added source line to its new-file line number."""

        added_lines: dict[str, dict[int, str]] = {}
        changed_files: set[str] = set()

        current_file: str | None = None
        new_line_number: int | None = None

        for line in diff.splitlines():
            if line.startswith("+++ "):
                match = self.FILE_HEADER_PATTERN.match(line)
                current_file = match.group(1) if match else None

                if current_file is not None:
                    changed_files.add(current_file)
                    added_lines.setdefault(current_file, {})

                new_line_number = None
                continue

            if line.startswith("--- "):
                # Old-file header, not a deleted source line.
                continue

            hunk_match = self.HUNK_HEADER_PATTERN.match(line)
            if hunk_match:
                new_line_number = int(hunk_match.group(1))
                continue

            if current_file is None or new_line_number is None:
                continue

            if line.startswith("\\ No newline at end of file"):
                continue

            if line.startswith("+"):
                # Added line: exclude the diff marker from source content.
                added_lines[current_file][new_line_number] = line[1:]
                new_line_number += 1
            elif line.startswith("-"):
                # Removed lines do not exist in the new file.
                continue
            elif line.startswith(" "):
                # Context lines exist in both old and new versions.
                new_line_number += 1

        return added_lines, changed_files

    def validate(
        self,
        finding: LLMReviewFinding,
        diff: str,
    ) -> FindingValidationResult:
        """Validate the finding against added lines in the supplied diff."""

        if not diff or not diff.strip():
            return FindingValidationResult(
                valid=False,
                errors=("The pull request diff is empty.",),
            )

        added_lines, changed_files = self._extract_added_lines(diff)
        errors: list[str] = []

        if finding.file_path not in changed_files:
            return FindingValidationResult(
                valid=False,
                errors=(
                    "The finding file path is not present in the changed files.",
                ),
            )

        file_added_lines = added_lines.get(finding.file_path, {})
        normalized_evidence = self._normalize_evidence(finding.evidence)

        if not normalized_evidence:
            errors.append("The finding evidence is empty.")
        else:
            matching_line_numbers = [
                line_number
                for line_number, source_line in file_added_lines.items()
                if source_line.strip() == normalized_evidence
            ]

            if not matching_line_numbers:
                errors.append(
                    "The quoted evidence does not match an added line in the diff."
                )

            if finding.line_number not in file_added_lines:
                errors.append(
                    "The reported line number is not an added line in the diff."
                )
            elif (
                file_added_lines[finding.line_number].strip()
                != normalized_evidence
            ):
                errors.append(
                    "The quoted evidence does not match the reported line number."
                )

        return FindingValidationResult(
            valid=not errors,
            errors=tuple(errors),
        )
