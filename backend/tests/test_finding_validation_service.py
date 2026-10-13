
from app.services.finding_validation_service import (
    FindingValidationService,
)
from app.services.llm_review_service import LLMReviewFinding


SAMPLE_DIFF = """\
diff --git a/frontend/src/styles.css b/frontend/src/styles.css
index 1111111..2222222 100644
--- a/frontend/src/styles.css
+++ b/frontend/src/styles.css
@@ -60,1 +60,1 @@
-  z-index: 50;
+  z-index: 60;
"""


def make_finding(
    *,
    file_path="frontend/src/styles.css",
    line_number=60,
    evidence="  z-index: 60;",
):
    return LLMReviewFinding(
        rule_id="LLM001",
        severity="medium",
        category="layering",
        classification="uncertain",
        message="Potential issue with header layering.",
        file_path=file_path,
        line_number=line_number,
        evidence=evidence,
        evidence_explanation="The changed value should be checked.",
        policy_sources=[],
    )


def test_accepts_valid_added_line_evidence():
    service = FindingValidationService()

    result = service.validate(
        finding=make_finding(),
        diff=SAMPLE_DIFF,
    )

    assert result.valid is True
    assert result.errors == ()


def test_rejects_evidence_not_present_in_added_lines():
    service = FindingValidationService()

    result = service.validate(
        finding=make_finding(evidence="z-index: 999;"),
        diff=SAMPLE_DIFF,
    )

    assert result.valid is False
    assert any(
        "does not match an added line" in error
        for error in result.errors
    )


def test_rejects_file_not_changed_in_diff():
    service = FindingValidationService()

    result = service.validate(
        finding=make_finding(file_path="frontend/src/other.css"),
        diff=SAMPLE_DIFF,
    )

    assert result.valid is False
    assert any(
        "file path" in error
        for error in result.errors
    )


def test_rejects_line_number_not_added_in_diff():
    service = FindingValidationService()

    result = service.validate(
        finding=make_finding(line_number=99),
        diff=SAMPLE_DIFF,
    )

    assert result.valid is False
    assert any(
        "line number" in error
        for error in result.errors
    )


def test_rejects_evidence_assigned_to_wrong_line():
    service = FindingValidationService()

    result = service.validate(
        finding=make_finding(
            line_number=60,
            evidence="some-other-code();",
        ),
        diff=SAMPLE_DIFF,
    )

    assert result.valid is False
    assert len(result.errors) >= 1


def test_rejects_empty_diff():
    service = FindingValidationService()

    result = service.validate(
        finding=make_finding(),
        diff="",
    )

    assert result.valid is False
    assert "The pull request diff is empty." in result.errors



def test_real_css_diff_maps_added_z_index_to_line_64():
    service = FindingValidationService()

    real_pr_diff = """\
diff --git a/frontend/src/styles.css b/frontend/src/styles.css
index 291edd5..2fae127 100644
--- a/frontend/src/styles.css
+++ b/frontend/src/styles.css
@@ -61,7 +61,7 @@ img {
 .header {
   position: sticky;
   top: 0;
-  z-index: 50;
+  z-index: 60;
   background: rgba(250, 249, 246, 0.96);
   border-bottom: 1px solid #e8e3da;
   backdrop-filter: blur(10px);
"""

    finding = make_finding(
        file_path="frontend/src/styles.css",
        line_number=64,
        evidence="  z-index: 60;",
    )

    result = service.validate(finding=finding, diff=real_pr_diff)

    assert result.valid is True
    assert result.errors == ()


def test_real_css_diff_rejects_hunk_start_as_added_line_number():
    service = FindingValidationService()

    real_pr_diff = """\
diff --git a/frontend/src/styles.css b/frontend/src/styles.css
index 291edd5..2fae127 100644
--- a/frontend/src/styles.css
+++ b/frontend/src/styles.css
@@ -61,7 +61,7 @@ img {
 .header {
   position: sticky;
   top: 0;
-  z-index: 50;
+  z-index: 60;
   background: rgba(250, 249, 246, 0.96);
   border-bottom: 1px solid #e8e3da;
   backdrop-filter: blur(10px);
"""

    finding = make_finding(
        file_path="frontend/src/styles.css",
        line_number=61,
        evidence="  z-index: 60;",
    )

    result = service.validate(finding=finding, diff=real_pr_diff)

    assert result.valid is False
    assert any(
        "line number" in error
        for error in result.errors
    )


def test_ts_async_fixture_uses_actual_added_line_number():
    from pathlib import Path

    fixture_path = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "fixtures"
        / "03_ts_async_error.diff"
    )
    diff = fixture_path.read_text(encoding="utf-8")
    service = FindingValidationService()

    correct_finding = make_finding(
        file_path="frontend/src/api.ts",
        line_number=2,
        evidence="return fetchProfile(userId);",
    )
    incorrect_finding = make_finding(
        file_path="frontend/src/api.ts",
        line_number=3,
        evidence="return fetchProfile(userId);",
    )

    correct_result = service.validate(
        finding=correct_finding,
        diff=diff,
    )
    incorrect_result = service.validate(
        finding=incorrect_finding,
        diff=diff,
    )

    assert correct_result.valid is True
    assert incorrect_result.valid is False
    assert any(
        "line number is not an added line" in error
        for error in incorrect_result.errors
    )

