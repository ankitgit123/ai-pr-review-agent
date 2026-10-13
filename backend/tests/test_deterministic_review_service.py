
import pytest

from app.services.deterministic_review_service import (
    DeterministicReviewService,
)


@pytest.fixture
def service():
    return DeterministicReviewService()


def test_detects_added_console_log_with_correct_location(service):
    diff = """diff --git a/src/app.ts b/src/app.ts
--- a/src/app.ts
+++ b/src/app.ts
@@ -1,2 +1,3 @@
 const ready = true;
+console.log("debug");
 export default ready;
"""

    result = service.review(diff)

    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.rule_id == "JS001"
    assert finding.severity == "low"
    assert finding.file_path == "src/app.ts"
    assert finding.line_number == 2
    assert finding.evidence == 'console.log("debug");'


@pytest.mark.parametrize(
    "file_path",
    [
        "src/app.js",
        "src/app.jsx",
        "src/app.ts",
        "src/app.tsx",
        "src/app.mjs",
        "src/app.cjs",
        "src/app.mts",
        "src/app.cts",
    ],
)
def test_detects_console_log_in_supported_extensions(service, file_path):
    diff = (
        f"diff --git a/{file_path} b/{file_path}\n"
        f"--- a/{file_path}\n"
        f"+++ b/{file_path}\n"
        "@@ -0,0 +1 @@\n"
        '+console.log("debug");\n'
    )

    result = service.review(diff)

    assert len(result.findings) == 1
    assert result.findings[0].file_path == file_path


def test_ignores_removed_console_log(service):
    diff = """diff --git a/src/app.js b/src/app.js
--- a/src/app.js
+++ b/src/app.js
@@ -1,2 +1 @@
-console.log("old debug");
 const ready = true;
"""

    result = service.review(diff)

    assert result.findings == []


def test_ignores_console_log_on_unchanged_line(service):
    diff = """diff --git a/src/app.js b/src/app.js
--- a/src/app.js
+++ b/src/app.js
@@ -1,2 +1,3 @@
 console.log("existing");
 const ready = true;
+export default ready;
"""

    result = service.review(diff)

    assert result.findings == []


def test_ignores_console_log_in_css(service):
    diff = """diff --git a/src/styles.css b/src/styles.css
--- a/src/styles.css
+++ b/src/styles.css
@@ -0,0 +1 @@
+console.log("debug");
"""

    result = service.review(diff)

    assert result.findings == []


def test_reports_each_added_console_log(service):
    diff = """diff --git a/src/app.ts b/src/app.ts
--- a/src/app.ts
+++ b/src/app.ts
@@ -0,0 +1,2 @@
+console.log("first");
+console.log("second");
"""

    result = service.review(diff)

    assert len(result.findings) == 2
    assert [finding.line_number for finding in result.findings] == [1, 2]


def test_summary_does_not_claim_code_is_bug_free(service):
    result = service.review("")

    assert result.findings == []
    assert "does not establish" in result.summary


def test_tracks_new_line_numbers_after_removed_lines(service):
    diff = """diff --git a/src/app.ts b/src/app.ts
--- a/src/app.ts
+++ b/src/app.ts
@@ -10,3 +10,3 @@
 const first = 1;
-const oldValue = 2;
+console.log("debug");
 const last = 3;
"""

    result = service.review(diff)

    assert len(result.findings) == 1
    assert result.findings[0].line_number == 11
