#!/usr/bin/env python3
"""Tests for validate-test-spec.py (D-27)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-test-spec.py")

VALID_DOC = """\
---
document_id: D-27
feature: "demo"
version: "1.0"
status: draft
---

# Demo — Test Specification

## 1. Overview
Đặc tả test cho feature demo.

## 2. Test Case Summary

| TC | Title | REQ |
|----|-------|-----|
| TC-001 | Tạo đơn hợp lệ | REQ-DEMO-001 |

## 3. Detailed Test Cases

### TC-001: Tạo đơn hợp lệ
- **REQ ID:** REQ-DEMO-001
- **Severity:** High

| Step | Action | Expected |
|------|--------|----------|
| 1 | Nhập đơn có 1 dòng | Đơn được tạo, trạng thái draft |

## 4. Coverage Matrix

| REQ | TC |
|-----|----|
| REQ-DEMO-001 | TC-001 |
"""


def run_script(doc_content: str) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-27-demo.md"
        doc_path.write_text(doc_content, encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout), result.returncode


def test_valid_document():
    result, code = run_script(VALID_DOC)
    assert code == 0, f"Expected 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["semantic_review"] == "n/a"
    assert result["passed"] is True


def test_missing_section():
    doc = VALID_DOC.replace("## 4. Coverage Matrix", "## 4. Removed")
    result, code = run_script(doc)
    assert code == 1
    assert any(i["type"] == "SECTION_MISSING" for i in result["issues"])


def test_no_test_cases():
    doc = VALID_DOC.replace("TC-001", "XX-001")
    result, code = run_script(doc)
    assert any(i["type"] == "NO_TEST_CASES" for i in result["issues"])


def test_tc_missing_severity():
    doc = VALID_DOC.replace("- **Severity:** High\n", "")
    result, code = run_script(doc)
    assert any(i["type"] == "TC_MISSING_SEVERITY" for i in result["issues"])


def test_tc_missing_req():
    doc = VALID_DOC.replace("- **REQ ID:** REQ-DEMO-001\n", "")
    result, code = run_script(doc)
    assert any(i["type"] == "TC_MISSING_REQ" for i in result["issues"])


def test_vietnamese_sections():
    doc = (VALID_DOC
           .replace("## 1. Overview", "## 1. Tổng quan")
           .replace("## 2. Test Case Summary", "## 2. Danh sách test case")
           .replace("## 3. Detailed Test Cases", "## 3. Chi tiết test case")
           .replace("## 4. Coverage Matrix", "## 4. Ma trận bao phủ"))
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"VI sections not recognized: {missing}"


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/D-27.md"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1


if __name__ == "__main__":
    tests = [test_valid_document, test_missing_section, test_no_test_cases,
             test_tc_missing_severity, test_tc_missing_req,
             test_vietnamese_sections, test_missing_document]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
