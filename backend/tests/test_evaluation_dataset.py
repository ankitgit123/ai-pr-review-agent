
import json
import re
from pathlib import Path

import pytest


EVALUATION_DIR = Path(__file__).resolve().parents[1] / "evaluation"
MANIFEST_PATH = EVALUATION_DIR / "manifest.json"


def extract_added_lines(diff: str) -> set[int]:
    """Extract new-file line numbers for added lines in a unified diff."""
    added_lines: set[int] = set()
    new_line_number: int | None = None

    hunk_pattern = re.compile(
        r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@"
    )

    for line in diff.splitlines():
        if line.startswith("+++ "):
            new_line_number = None
            continue

        if line.startswith("--- "):
            continue

        match = hunk_pattern.match(line)
        if match:
            new_line_number = int(match.group(1))
            continue

        if new_line_number is None:
            continue

        if line.startswith("\\ No newline at end of file"):
            continue

        if line.startswith("+"):
            added_lines.add(new_line_number)
            new_line_number += 1
        elif line.startswith("-"):
            continue
        elif line.startswith(" "):
            new_line_number += 1

    return added_lines


@pytest.fixture(scope="module")
def manifest():
    assert MANIFEST_PATH.is_file(), (
        f"Evaluation manifest not found: {MANIFEST_PATH}"
    )
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_contains_six_cases(manifest):
    assert manifest["dataset_version"] == 1
    assert len(manifest["cases"]) == 6


def test_case_ids_are_unique(manifest):
    case_ids = [case["id"] for case in manifest["cases"]]
    assert len(case_ids) == len(set(case_ids))


@pytest.mark.parametrize(
    "case_id",
    [
        "css_layering",
        "js_null_dereference",
        "ts_async_error",
        "python_authorization",
        "sql_tenant_isolation",
        "harmless_refactor",
    ],
)
def test_fixture_exists_and_contains_expected_added_lines(
    manifest, case_id
):
    case = next(
        (item for item in manifest["cases"] if item["id"] == case_id),
        None,
    )
    assert case is not None, f"Missing evaluation case: {case_id}"

    fixture_path = EVALUATION_DIR / case["fixture"]
    assert fixture_path.is_file(), (
        f"Fixture not found for {case_id}: {fixture_path}"
    )

    diff = fixture_path.read_text(encoding="utf-8")
    added_lines = extract_added_lines(diff)

    assert case["expected_added_lines"], (
        f"{case_id} must define expected added lines"
    )
    assert set(case["expected_added_lines"]).issubset(added_lines), (
        f"{case_id}: expected added lines "
        f"{case['expected_added_lines']}, found {sorted(added_lines)}"
    )
