#!/usr/bin/env python3
"""Tests for validate-acceptance-check.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "validate_acceptance_check",
    os.path.join(os.path.dirname(__file__), "..", "validate-acceptance-check.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

validate = mod.validate
check_sections = mod.check_sections
check_decision = mod.check_decision
check_criteria_checklist = mod.check_criteria_checklist
check_traceability_summary = mod.check_traceability_summary


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


MINIMAL_VALID = """---
title: "Acceptance Report"
decided_at: "2026-05-28"
decided_by: "PM"
decision: "ACCEPTED"
---

# Acceptance Report

## Acceptance Criteria Checklist

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All requirements traced | PASS | matrix.md — 100% |
| All tests passed | PASS | execution-report.md — 50/50 |
| Coverage meets threshold | PASS | 85% >= 80% |

## Traceability Summary

| Metric | Value |
|--------|-------|
| Total Requirements | 15 |
| Designed | 15 |
| Implemented | 15 |
| Tested | 15 |
| Trace Coverage | 100% |

## Decision

**Status:** ACCEPTED
**Decided by:** PM
**Reason:** All acceptance criteria met. Full traceability achieved.
"""

REJECTED_VALID = """---
title: "Acceptance Report"
decided_at: "2026-05-28"
decided_by: "PM"
decision: "REJECTED"
---

# Acceptance Report

## Acceptance Criteria Checklist

| Criterion | Status | Evidence |
|-----------|--------|----------|
| All requirements traced | PASS | matrix.md — 100% |
| All tests passed | FAIL | 2 failures |
| Coverage meets threshold | PASS | 85% >= 80% |

## Traceability Summary

| Metric | Value |
|--------|-------|
| Total Requirements | 15 |
| Designed | 15 |
| Implemented | 15 |
| Tested | 13 |
| Trace Coverage | 87% |

## Decision

**Status:** REJECTED
**Decided by:** PM
**Reason:** 2 test failures and incomplete test coverage.

## Action Items

| Item | Phase | Description | Priority |
|------|-------|-------------|----------|
| Fix user creation bug | Phase 3 | code_bug in test_user_create | High |
| Add missing test cases | Phase 2 | 2 requirements lack test coverage | Medium |
"""


class TestCheckSections:
    def test_all_present(self):
        issues = check_sections(MINIMAL_VALID)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 0

    def test_missing_decision(self):
        content = MINIMAL_VALID.replace("## Decision", "## Other")
        issues = check_sections(content)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert any(i["section"] == "Decision" for i in missing)


class TestCheckDecision:
    def test_valid_accepted(self):
        issues = check_decision(MINIMAL_VALID)
        assert len(issues) == 0

    def test_valid_rejected_with_actions(self):
        issues = check_decision(REJECTED_VALID)
        assert len(issues) == 0

    def test_no_decision(self):
        content = "# Report\n\nNo decision here."
        issues = check_decision(content)
        assert any(i["type"] == "NO_DECISION" for i in issues)

    def test_missing_decided_by(self):
        content = MINIMAL_VALID.replace("**Decided by:** PM", "**Decided by:**")
        issues = check_decision(content)
        assert any(i["type"] == "NO_DECIDED_BY" for i in issues)

    def test_missing_reason(self):
        content = MINIMAL_VALID.replace(
            "**Reason:** All acceptance criteria met. Full traceability achieved.",
            "**Reason:**",
        )
        issues = check_decision(content)
        assert any(i["type"] == "NO_REASON" for i in issues)

    def test_rejected_without_actions(self):
        content = REJECTED_VALID.replace("## Action Items", "## Other")
        content = content.replace(
            "| Fix user creation bug | Phase 3 | code_bug in test_user_create | High |\n| Add missing test cases | Phase 2 | 2 requirements lack test coverage | Medium |",
            "",
        )
        issues = check_decision(content)
        assert any(i["type"] == "REJECTED_NO_ACTIONS" for i in issues)


class TestCheckCriteriaChecklist:
    def test_has_criteria(self):
        issues = check_criteria_checklist(MINIMAL_VALID)
        assert len(issues) == 0

    def test_empty_checklist(self):
        content = MINIMAL_VALID.replace(
            "| All requirements traced | PASS | matrix.md — 100% |\n"
            "| All tests passed | PASS | execution-report.md — 50/50 |\n"
            "| Coverage meets threshold | PASS | 85% >= 80% |",
            "",
        )
        issues = check_criteria_checklist(content)
        assert any(i["type"] == "EMPTY_CHECKLIST" for i in issues)


# Vietnamese checklist section ("Danh sách tiêu chí nghiệm thu").
CHECKLIST_VN_EMPTY = """# Báo cáo nghiệm thu

## Danh sách tiêu chí nghiệm thu

| Tiêu chí | Trạng thái | Bằng chứng |
|----------|------------|------------|

## Tóm tắt truy vết
"""

CHECKLIST_VN_FILLED = """# Báo cáo nghiệm thu

## Danh sách tiêu chí nghiệm thu

| Tiêu chí | Trạng thái | Bằng chứng |
|----------|------------|------------|
| Mọi yêu cầu được truy vết | PASS | matrix.md — 100% |

## Tóm tắt truy vết
"""


class TestCriteriaChecklistVietnamese:
    def test_empty_vn_checklist_flagged(self):
        # Bug A4: header-only VN checklist passed because the English-only header
        # detection ("Criterion"/"Status") counted the VN header row as data.
        issues = check_criteria_checklist(CHECKLIST_VN_EMPTY)
        assert any(i["type"] == "EMPTY_CHECKLIST" for i in issues)

    def test_filled_vn_checklist_ok(self):
        issues = check_criteria_checklist(CHECKLIST_VN_FILLED)
        assert issues == []


class TestCheckTraceabilitySummary:
    def test_has_summary(self):
        issues = check_traceability_summary(MINIMAL_VALID)
        assert len(issues) == 0

    def test_missing_total(self):
        content = MINIMAL_VALID.replace("| Total Requirements | 15 |", "| Other | 15 |")
        issues = check_traceability_summary(content)
        assert any(i["type"] == "NO_REQ_TOTAL" for i in issues)

    def test_missing_coverage(self):
        content = MINIMAL_VALID.replace("| Trace Coverage | 100% |", "| Other | 100% |")
        issues = check_traceability_summary(content)
        assert any(i["type"] == "NO_TRACE_COVERAGE" for i in issues)


class TestFullValidation:
    def test_valid_accepted(self, tmp_path):
        path = str(tmp_path / "acceptance.md")
        _write(path, MINIMAL_VALID)
        result = validate(path)
        assert result["valid"] is True
        assert result["decision"] == "ACCEPTED"

    def test_valid_rejected(self, tmp_path):
        path = str(tmp_path / "acceptance.md")
        _write(path, REJECTED_VALID)
        result = validate(path)
        assert result["valid"] is True
        assert result["decision"] == "REJECTED"

    def test_invalid_document(self, tmp_path):
        path = str(tmp_path / "acceptance.md")
        _write(path, "# Empty\n\nNo acceptance.")
        result = validate(path)
        assert result["valid"] is False

    def test_cli_exit_code(self, tmp_path):
        import subprocess

        path = str(tmp_path / "acceptance.md")
        _write(path, MINIMAL_VALID)
        script = os.path.join(
            os.path.dirname(__file__), "..", "validate-acceptance-check.py"
        )
        result = subprocess.run([sys.executable, script, path], capture_output=True)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True
