#!/usr/bin/env python3
"""Tests for validate-test-plan.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "validate_test_plan",
    os.path.join(os.path.dirname(__file__), "..", "validate-test-plan.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

validate = mod.validate
check_sections = mod.check_sections
check_entry_exit_criteria = mod.check_entry_exit_criteria
check_risk_table = mod.check_risk_table
check_schedule = mod.check_schedule


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


MINIMAL_VALID = """---
document_id: D-26
title: "Test"
---

# Test

## 1. (Overview)

Test plan for the Test project.

## 2. (Test Scope)

All REQ-001 through REQ-010 requirements.

## 3. (Test Levels)

Unit, Integration, System, E2E.

## 4. (Test Approach)

TDD with regression suite.

## 5. (Test Environment)

Docker-based test environment.

## 6. (Entry & Exit Criteria)

### 6.1 (Entry Criteria)

All Phase 2 artifacts approved.

### 6.2 (Exit Criteria)

80% code coverage, all critical tests pass.

## 7. (Schedule)

### 7.1 (Milestones)

| Milestone | Target Date | Dependencies |
|-----------|------------|--------------|
| Unit tests complete | 2026-06-15 | Implementation done |

### 7.2 (Gantt Chart)

```mermaid
gantt
    title Test Schedule
    dateFormat YYYY-MM-DD
    section Unit Tests
    Write unit tests: 2026-06-01, 14d
```

## 8. (Team & Roles)

QA lead: Test design and execution.

## 9. (Risk Management)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Test data unavailable | Medium | High | Prepare mock data early |

## 10. (Deliverables)

D-26 Test Plan, D-27 Test Specification, Test Execution Report.
"""


class TestCheckSections:
    def test_all_sections_present(self):
        issues = check_sections(MINIMAL_VALID)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 0

    def test_missing_section(self):
        content = MINIMAL_VALID.replace(
            "## 9. (Risk Management)\n\n| Risk | Likelihood | Impact | Mitigation |\n|------|-----------|--------|------------|\n| Test data unavailable | Medium | High | Prepare mock data early |\n",
            "",
        )
        issues = check_sections(content)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 1
        assert missing[0]["section"] == "Risk"


class TestEntryExitCriteria:
    def test_both_present(self):
        issues = check_entry_exit_criteria(MINIMAL_VALID)
        assert len(issues) == 0

    def test_missing_entry(self):
        content = MINIMAL_VALID.replace("### 6.1 (Entry Criteria)", "### 6.1 Something Else")
        issues = check_entry_exit_criteria(content)
        entry_issues = [i for i in issues if i["type"] == "NO_ENTRY_CRITERIA"]
        assert len(entry_issues) == 1

    def test_missing_exit(self):
        content = MINIMAL_VALID.replace("Exit Criteria", "Other Criteria")
        issues = check_entry_exit_criteria(content)
        exit_issues = [i for i in issues if i["type"] == "NO_EXIT_CRITERIA"]
        assert len(exit_issues) == 1


class TestRiskTable:
    def test_has_risks(self):
        issues = check_risk_table(MINIMAL_VALID)
        assert len(issues) == 0

    def test_empty_risk_table(self):
        content = MINIMAL_VALID.replace(
            "| Test data unavailable | Medium | High | Prepare mock data early |",
            "",
        )
        issues = check_risk_table(content)
        empty = [i for i in issues if i["type"] == "EMPTY_RISK_TABLE"]
        assert len(empty) == 1


class TestSchedule:
    def test_has_gantt(self):
        issues = check_schedule(MINIMAL_VALID)
        assert len(issues) == 0

    def test_no_schedule(self):
        content = "# Plan\n\n## Schedule\n\nTBD."
        issues = check_schedule(content)
        no_sched = [i for i in issues if i["type"] == "NO_SCHEDULE"]
        assert len(no_sched) == 1


# Vietnamese-language sections (the actual generated document_output_language).
# Risk table empty; schedule has a VN milestone table ("Cột mốc") and NO gantt.
RISK_VN_EMPTY = """# Kế hoạch kiểm thử

## 9. Quản lý rủi ro

| Rủi ro | Khả năng | Tác động | Giảm thiểu |
|--------|----------|----------|------------|

## 10. Sản phẩm bàn giao
"""

RISK_VN_FILLED = """# Kế hoạch kiểm thử

## 9. Quản lý rủi ro

| Rủi ro | Khả năng | Tác động | Giảm thiểu |
|--------|----------|----------|------------|
| Thiếu dữ liệu test | Trung bình | Cao | Chuẩn bị mock sớm |

## 10. Sản phẩm bàn giao
"""

SCHEDULE_VN_TABLE_ONLY = """# Kế hoạch kiểm thử

## 7. Lịch trình

### 7.1 Cột mốc

| Cột mốc | Ngày mục tiêu | Phụ thuộc |
|---------|---------------|-----------|
| Xong unit test | 2026-06-15 | Hoàn tất triển khai |

## 8. Đội ngũ
"""

SCHEDULE_VN_NONE = """# Kế hoạch kiểm thử

## 7. Lịch trình

Chưa xác định.

## 8. Đội ngũ
"""


class TestRiskTableVietnamese:
    def test_empty_vn_risk_table_flagged(self):
        # Bug A1: English-only "#+\\s.*Risk" missed the VN heading → empty table passed.
        issues = check_risk_table(RISK_VN_EMPTY)
        assert [i for i in issues if i["type"] == "EMPTY_RISK_TABLE"]

    def test_filled_vn_risk_table_ok(self):
        issues = check_risk_table(RISK_VN_FILLED)
        assert issues == []


class TestScheduleVietnamese:
    def test_vn_milestone_table_counts(self):
        # Bug A2: English-only "| Milestone |" missed the VN "Cột mốc" table.
        issues = check_schedule(SCHEDULE_VN_TABLE_ONLY)
        assert [i for i in issues if i["type"] == "NO_SCHEDULE"] == []

    def test_vn_no_schedule_flagged(self):
        issues = check_schedule(SCHEDULE_VN_NONE)
        assert [i for i in issues if i["type"] == "NO_SCHEDULE"]


class TestFullValidation:
    def test_valid_document(self, tmp_path):
        path = str(tmp_path / "d26.md")
        _write(path, MINIMAL_VALID)
        result = validate(path)
        assert result["valid"] is True

    def test_invalid_document(self, tmp_path):
        path = str(tmp_path / "d26.md")
        _write(path, "# Empty plan\n\nNothing.")
        result = validate(path)
        assert result["valid"] is False

    def test_cli_exit_code(self, tmp_path):
        import subprocess

        path = str(tmp_path / "d26.md")
        _write(path, MINIMAL_VALID)
        script = os.path.join(os.path.dirname(__file__), "..", "validate-test-plan.py")
        result = subprocess.run([sys.executable, script, path], capture_output=True)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True
