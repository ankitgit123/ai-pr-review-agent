
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReviewFinding(BaseModel):
    """One finding produced by a review rule."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str
    severity: Literal["low", "medium", "high", "critical"]
    category: str
    message: str
    file_path: str
    line_number: int = Field(gt=0)
    evidence: str


class DeterministicReviewResult(BaseModel):
    """Structured result from deterministic diff inspection."""

    model_config = ConfigDict(extra="forbid")

    engine: Literal["deterministic"] = "deterministic"
    files_changed: list[str]
    findings: list[ReviewFinding]
    summary: str


class DeterministicReviewService:
    """Inspect added JavaScript and TypeScript lines using explicit rules."""

    JS_TS_EXTENSIONS = (
        ".js", ".jsx", ".ts", ".tsx",
        ".mjs", ".cjs", ".mts", ".cts",
    )

    CONSOLE_LOG_PATTERN = re.compile(r"\bconsole\s*\.\s*log\s*\(")
    HUNK_PATTERN = re.compile(
        r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@"
    )

    def review(self, diff: str) -> DeterministicReviewResult:
        files_changed: list[str] = []
        findings: list[ReviewFinding] = []

        current_file: str | None = None
        current_line_number: int | None = None

        for line in diff.splitlines():
            if line.startswith("+++ "):
                path = line[4:].strip()

                if path == "/dev/null":
                    current_file = None
                elif path.startswith("b/"):
                    current_file = path[2:]
                else:
                    current_file = path

                if current_file and current_file not in files_changed:
                    files_changed.append(current_file)

                current_line_number = None
                continue

            if line.startswith("--- "):
                continue

            if line.startswith("@@ "):
                match = self.HUNK_PATTERN.match(line)
                current_line_number = (
                    int(match.group(1)) if match else None
                )
                continue

            if current_line_number is None:
                continue

            if line.startswith("+") and not line.startswith("+++"):
                added_code = line[1:]

                if (
                    current_file
                    and current_file.lower().endswith(self.JS_TS_EXTENSIONS)
                    and self.CONSOLE_LOG_PATTERN.search(added_code)
                ):
                    findings.append(
                        ReviewFinding(
                            rule_id="JS001",
                            severity="low",
                            category="debugging",
                            message=(
                                "New console.log statement detected. "
                                "Confirm whether it should remain in production code."
                            ),
                            file_path=current_file,
                            line_number=current_line_number,
                            evidence=added_code.strip(),
                        )
                    )

                current_line_number += 1

            elif line.startswith("-"):
                continue

            else:
                current_line_number += 1

        if findings:
            summary = (
                f"Found {len(findings)} finding(s) across "
                f"{len(files_changed)} changed file(s)."
            )
        else:
            summary = (
                "No findings from the currently implemented deterministic rules. "
                "This does not establish that the changes are bug-free."
            )

        return DeterministicReviewResult(
            files_changed=files_changed,
            findings=findings,
            summary=summary,
        )
