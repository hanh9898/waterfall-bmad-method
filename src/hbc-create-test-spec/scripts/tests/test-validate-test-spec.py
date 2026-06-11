#!/usr/bin/env python3
"""Tests for validate-test-spec.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "validate_test_spec",
    os.path.join(os.path.dirname(__file__), "..", "validate-test-spec.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

validate = mod.validate
check_sections = mod.check_sections
check_tc_ids = mod.check_tc_ids
check_req_coverage = mod.check_req_coverage
check_tc_fields = mod.check_tc_fields


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


MINIMAL_VALID = """---
document_id: D-27
title: "Test"
---

# Test

## 1. (Overview)

Test specification for the Test project.

## 2. (Test Case Summary)

| TC ID | Category | REQ ID | Description | Severity | Status |
|-------|----------|--------|-------------|----------|--------|
| TC-001 | Functional | REQ-001 | User login | High | - |
| TC-002 | Functional | REQ-002 | User registration | High | - |
| TC-003 | Functional | REQ-001 | Login failure | Medium | - |

## 3. (Detailed Test Cases)

### TC-001: User login success

**REQ ID:** REQ-001
**Category:** Functional
**Severity:** High
**Preconditions:**

- User account exists

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Navigate to login page | Login form displayed |
| 2 | Enter valid credentials | Form accepts input |
| 3 | Click submit | Redirected to dashboard |

### TC-002: User registration

**REQ ID:** REQ-002
**Category:** Functional
**Severity:** High
**Preconditions:**

- No existing account with test email

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Navigate to register page | Registration form displayed |
| 2 | Fill in required fields | Form validates input |
| 3 | Submit form | Account created, confirmation shown |

### TC-003: Login failure with wrong password

**REQ ID:** REQ-001
**Category:** Functional
**Severity:** Medium
**Preconditions:**

- User account exists

**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Navigate to login page | Login form displayed |
| 2 | Enter wrong password | Form accepts input |
| 3 | Click submit | Error message shown |

## 4. (Coverage Matrix)

| REQ ID | Requirement | Test Cases | Coverage |
|--------|-------------|------------|----------|
| REQ-001 | User login | TC-001, TC-003 | 100% |
| REQ-002 | User registration | TC-002 | 100% |
"""


class TestCheckSections:
    def test_all_sections_present(self):
        issues = check_sections(MINIMAL_VALID)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 0

    def test_missing_section(self):
        content = MINIMAL_VALID.replace("(Coverage Matrix)", "(Other)")
        issues = check_sections(content)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 1
        assert missing[0]["section"] == "Coverage Matrix"


class TestCheckTcIds:
    def test_valid_ids(self):
        issues = check_tc_ids(MINIMAL_VALID)
        assert len(issues) == 0

    def test_no_test_cases(self):
        issues = check_tc_ids("# Empty document\n\nNo test cases.")
        no_tc = [i for i in issues if i["type"] == "NO_TEST_CASES"]
        assert len(no_tc) == 1

    def test_duplicate_tc(self):
        content = "TC-001 first\nTC-001 second\nTC-002 third"
        issues = check_tc_ids(content)
        dups = [i for i in issues if i["type"] == "TC_ID_DUPLICATE"]
        assert len(dups) == 1

    def test_gap_in_tc_ids(self):
        content = "TC-001 first\nTC-003 third"
        issues = check_tc_ids(content)
        gaps = [i for i in issues if i["type"] == "TC_ID_GAP"]
        assert len(gaps) == 1
        assert "TC-002" in gaps[0]["missing_ids"]


class TestReqCoverage:
    def test_full_coverage(self, tmp_path):
        d02 = str(tmp_path / "D-02.md")
        _write(d02, "REQ-001 Login\nREQ-002 Register\n")
        issues = check_req_coverage(MINIMAL_VALID, d02)
        assert len(issues) == 0

    def test_uncovered_req(self, tmp_path):
        d02 = str(tmp_path / "D-02.md")
        _write(d02, "REQ-001 Login\nREQ-002 Register\nREQ-003 Profile\n")
        issues = check_req_coverage(MINIMAL_VALID, d02)
        uncovered = [i for i in issues if i["type"] == "REQ_NO_COVERAGE"]
        assert len(uncovered) == 1
        assert uncovered[0]["req_id"] == "REQ-003"

    def test_orphan_ref(self, tmp_path):
        d02 = str(tmp_path / "D-02.md")
        _write(d02, "REQ-001 Login\n")
        issues = check_req_coverage(MINIMAL_VALID, d02)
        orphans = [i for i in issues if i["type"] == "ORPHAN_REQ_REF"]
        assert len(orphans) == 1
        assert orphans[0]["req_id"] == "REQ-002"

    def test_no_d02_no_issues(self):
        issues = check_req_coverage(MINIMAL_VALID, None)
        assert len(issues) == 0


class TestTcFields:
    def test_all_fields_present(self):
        issues = check_tc_fields(MINIMAL_VALID)
        assert len(issues) == 0

    def test_missing_req_field(self):
        content = MINIMAL_VALID.replace("**REQ ID:** REQ-001\n**Category:** Functional\n**Severity:** High", "**Category:** Functional\n**Severity:** High")
        issues = check_tc_fields(content)
        missing_req = [i for i in issues if i["type"] == "TC_MISSING_REQ"]
        assert len(missing_req) >= 1

    def test_missing_severity(self):
        content = MINIMAL_VALID.replace(
            "**Severity:** High\n**Preconditions:**\n\n- User account exists\n\n**Test Steps:**\n\n| Step | Action | Expected Result |\n|------|--------|----------------|\n| 1 | Navigate to login page | Login form displayed |\n| 2 | Enter valid credentials | Form accepts input |\n| 3 | Click submit | Redirected to dashboard |\n\n### TC-002",
            "**Preconditions:**\n\n- User account exists\n\n**Test Steps:**\n\n| Step | Action | Expected Result |\n|------|--------|----------------|\n| 1 | Navigate to login page | Login form displayed |\n| 2 | Enter valid credentials | Form accepts input |\n| 3 | Click submit | Redirected to dashboard |\n\n### TC-002",
        )
        issues = check_tc_fields(content)
        missing_sev = [i for i in issues if i["type"] == "TC_MISSING_SEVERITY"]
        assert len(missing_sev) >= 1


class TestFullValidation:
    def test_valid_document(self, tmp_path):
        path = str(tmp_path / "d27.md")
        _write(path, MINIMAL_VALID)
        d02 = str(tmp_path / "D-02.md")
        _write(d02, "REQ-001 Login\nREQ-002 Register\n")
        result = validate(path, d02)
        assert result["valid"] is True
        assert result["tc_count"] == 3
        assert result["req_coverage_pct"] == 100

    def test_invalid_document(self, tmp_path):
        path = str(tmp_path / "d27.md")
        _write(path, "# Empty spec")
        result = validate(path)
        assert result["valid"] is False

    def test_cli_exit_code(self, tmp_path):
        import subprocess

        path = str(tmp_path / "d27.md")
        _write(path, MINIMAL_VALID)
        script = os.path.join(os.path.dirname(__file__), "..", "validate-test-spec.py")
        result = subprocess.run([sys.executable, script, path], capture_output=True)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True


# --- F1: TC detection now matches the shared iter_tc_blocks (fence-aware, levels 3-6) ---

class TestF1SharedTcDetection:
    def test_h4_tc_heading_detected(self):
        # A `#### TC-` (4-hash) heading is now seen (was missed by `^### TC-`).
        content = "## 3. Detail\n\n#### TC-001: a\n**REQ ID:** REQ-001\n**Severity:** High\n"
        ids = check_tc_ids(content)
        assert not [i for i in ids if i["type"] == "NO_TEST_CASES"]
        fields = check_tc_fields(content)
        assert not [i for i in fields if i["type"] == "TC_MISSING_REQ"]

    def test_fenced_tc_example_not_counted(self):
        # A `### TC-` inside a ``` fence is an example, not a real test case.
        content = (
            "## 3. Detail\n\n```\n### TC-999: example\n**REQ ID:** REQ-999\n```\n\n"
            "### TC-001: real\n**REQ ID:** REQ-001\n**Severity:** High\n"
        )
        nums = sorted(n for n, _ in mod._tc_blocks_with_num(content))
        assert nums == [1]  # TC-999 inside the fence is excluded

    def test_empty_req_id_field_treated_as_missing(self):
        # tc_field returns None for a bare empty **REQ ID:** → flagged missing,
        # consistent with the readiness/facet engines.
        content = "## 3. Detail\n\n### TC-001: a\n**REQ ID:**\n**Severity:** High\n"
        fields = check_tc_fields(content)
        assert [i for i in fields if i["type"] == "TC_MISSING_REQ"]
