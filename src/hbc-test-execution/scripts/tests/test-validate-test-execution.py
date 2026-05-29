#!/usr/bin/env python3
"""Tests for validate-test-execution.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "validate_test_execution",
    os.path.join(os.path.dirname(__file__), "..", "validate-test-execution.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

validate = mod.validate
check_sections = mod.check_sections
check_summary = mod.check_summary
check_coverage = mod.check_coverage
check_defect_triage = mod.check_defect_triage


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


MINIMAL_VALID = """---
title: "Test Execution Report"
executed_at: "2026-05-28"
status: "PASS"
---

# Test Execution Report

## Test Execution Summary

| Metric | Value |
|--------|-------|
| Total Tests | 50 |
| Passed | 50 |
| Failed | 0 |
| Skipped | 0 |
| Coverage | 85% |

## Failed Tests Detail

No failed tests.

## Defect Triage

No defects to triage.
"""

VALID_WITH_FAILURES = """---
title: "Test Execution Report"
executed_at: "2026-05-28"
status: "FAIL"
---

# Test Execution Report

## Test Execution Summary

| Metric | Value |
|--------|-------|
| Total Tests | 50 |
| Passed | 48 |
| Failed | 2 |
| Skipped | 0 |
| Coverage | 82% |

## Failed Tests Detail

| test_id | test_case_ref | error | classification |
|---------|---------------|-------|----------------|
| test_user_create | TC-001 | AssertionError | code_bug |
| test_order_api | TC-004 | ConnectionError | environment |

## Defect Triage

| defect_id | type | action | assigned_to |
|-----------|------|--------|-------------|
| DEF-001 | code_bug | Return to Phase 3 | Dev |
| DEF-002 | environment | Fix environment | DevOps |
"""


class TestCheckSections:
    def test_all_present(self):
        issues = check_sections(MINIMAL_VALID)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 0

    def test_missing_section(self):
        content = MINIMAL_VALID.replace("## Failed Tests Detail", "## Other Section")
        issues = check_sections(content)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 1
        assert missing[0]["section"] == "失敗テスト詳細"


class TestCheckSummary:
    def test_valid_summary(self):
        issues = check_summary(MINIMAL_VALID)
        assert len(issues) == 0

    def test_no_total(self):
        content = "# Report\n\n## Test Execution Summary\n\nNo data."
        issues = check_summary(content)
        assert any(i["type"] == "NO_SUMMARY_TOTAL" for i in issues)

    def test_zero_tests(self):
        content = MINIMAL_VALID.replace("| Total Tests | 50 |", "| Total Tests | 0 |")
        issues = check_summary(content)
        assert any(i["type"] == "ZERO_TESTS" for i in issues)

    def test_inconsistent_counts(self):
        content = MINIMAL_VALID.replace(
            "| Passed | 50 |", "| Passed | 60 |"
        )
        issues = check_summary(content)
        assert any(i["type"] == "INCONSISTENT_COUNTS" for i in issues)


class TestCheckCoverage:
    def test_above_threshold(self):
        issues = check_coverage(MINIMAL_VALID, 80.0)
        assert len(issues) == 0

    def test_below_threshold(self):
        content = MINIMAL_VALID.replace("| Coverage | 85% |", "| Coverage | 60% |")
        issues = check_coverage(content, 80.0)
        assert any(i["type"] == "COVERAGE_BELOW_THRESHOLD" for i in issues)

    def test_no_coverage(self):
        content = MINIMAL_VALID.replace("| Coverage | 85% |", "")
        issues = check_coverage(content, 80.0)
        assert any(i["type"] == "NO_COVERAGE" for i in issues)


class TestCheckDefectTriage:
    def test_no_failures_no_triage_needed(self):
        issues = check_defect_triage(MINIMAL_VALID)
        assert len(issues) == 0

    def test_failures_with_complete_triage(self):
        issues = check_defect_triage(VALID_WITH_FAILURES)
        assert len(issues) == 0

    def test_failures_with_incomplete_triage(self):
        content = VALID_WITH_FAILURES.replace(
            "| DEF-002 | environment | Fix environment | DevOps |", ""
        )
        issues = check_defect_triage(content)
        assert any(i["type"] == "INCOMPLETE_TRIAGE" for i in issues)


class TestFullValidation:
    def test_valid_pass(self, tmp_path):
        path = str(tmp_path / "report.md")
        _write(path, MINIMAL_VALID)
        result = validate(path)
        assert result["valid"] is True
        assert result["summary"]["total"] == 50
        assert result["summary"]["passed"] == 50

    def test_valid_with_failures(self, tmp_path):
        path = str(tmp_path / "report.md")
        _write(path, VALID_WITH_FAILURES)
        result = validate(path)
        assert result["valid"] is True
        assert result["summary"]["failed"] == 2

    def test_invalid_document(self, tmp_path):
        path = str(tmp_path / "report.md")
        _write(path, "# Empty report\n\nNothing.")
        result = validate(path)
        assert result["valid"] is False

    def test_cli_exit_code(self, tmp_path):
        import subprocess

        path = str(tmp_path / "report.md")
        _write(path, MINIMAL_VALID)
        script = os.path.join(os.path.dirname(__file__), "..", "validate-test-execution.py")
        result = subprocess.run([sys.executable, script, path], capture_output=True)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True
