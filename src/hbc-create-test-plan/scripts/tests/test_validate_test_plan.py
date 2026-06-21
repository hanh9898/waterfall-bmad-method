#!/usr/bin/env python3
"""Tests for validate-test-plan.py (D-26)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-test-plan.py")

VALID_DOC = """\
---
document_id: D-26
feature: "demo"
version: "1.0"
status: draft
---

# Demo — Test Plan

## 1. Overview
Kế hoạch kiểm thử cho feature demo.

## 2. Test Scope
In-scope: tạo đơn. Out-of-scope: thanh toán.

## 3. Test Levels
Unit, integration, e2e.

## 4. Test Approach
Specification-based: decision-table cho business-rule.

## 5. Test Environment
Staging với dữ liệu mẫu.

## 6. Entry & Exit Criteria

### Entry Criteria
D-27 đã duyệt; build xanh.

### Exit Criteria
100% test-case critical pass.

## 7. Schedule

| Milestone | Date |
|-----------|------|
| Test design xong | 2026-07-01 |

## 8. Team & Roles

| Role | Person |
|------|--------|
| Tester | A |

## 9. Risk Management

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Dữ liệu test thiếu | Medium | High | Chuẩn bị fixture sớm |

## 10. Deliverables
Test execution report, acceptance report.
"""


def run_script(doc_content: str) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-26-demo.md"
        doc_path.write_text(doc_content, encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout), result.returncode


def test_valid_document():
    result, code = run_script(VALID_DOC)
    assert code == 0, f"Expected 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["structure_ok"] is True
    assert result["semantic_review"] == "n/a"
    assert result["passed"] is True


def test_churn_reported():
    # T2.11: validator exposes revision-history churn (no revision rows here → 0).
    result, code = run_script(VALID_DOC)
    assert "churn" in result
    assert result["churn"]["revisions"] == 0
    assert result["churn"]["high_churn"] is False


def test_high_churn_flagged():
    # A revision history with >threshold (4) dated rows is high-churn (RCA #1).
    rows = "".join(
        f"| 1.{i} | 2026-06-{10 + i:02d} | T | edit {i} |\n" for i in range(6)
    )
    doc = VALID_DOC + (
        "\n## Revision History\n\n"
        "| Version | Date | Author | Scope of Change |\n"
        "|---------|------|--------|----------------|\n" + rows
    )
    result, code = run_script(doc)
    assert result["churn"]["revisions"] == 6
    assert result["churn"]["high_churn"] is True


def test_missing_section():
    doc = VALID_DOC.replace("## 9. Risk Management", "## 9. Removed")
    result, code = run_script(doc)
    assert code == 1
    assert any(i["type"] == "SECTION_MISSING" for i in result["issues"])


def test_no_exit_criteria():
    # remove every "Exit Criteria" mention (section title + subheading) so the check fires
    doc = VALID_DOC.replace("Exit Criteria", "Closing")
    result, code = run_script(doc)
    assert any(i["type"] == "NO_EXIT_CRITERIA" for i in result["issues"])


def test_empty_risk_table():
    doc = VALID_DOC.replace(
        "| Dữ liệu test thiếu | Medium | High | Chuẩn bị fixture sớm |\n", ""
    )
    result, code = run_script(doc)
    assert any(i["type"] == "EMPTY_RISK_TABLE" for i in result["issues"])


def test_vietnamese_sections():
    doc = (VALID_DOC
           .replace("## 1. Overview", "## 1. Tổng quan")
           .replace("## 2. Test Scope", "## 2. Phạm vi kiểm thử")
           .replace("## 3. Test Levels", "## 3. Cấp độ kiểm thử")
           .replace("## 4. Test Approach", "## 4. Phương pháp kiểm thử")
           .replace("## 5. Test Environment", "## 5. Môi trường kiểm thử")
           .replace("## 6. Entry & Exit Criteria", "## 6. Tiêu chí vào/ra")
           .replace("## 7. Schedule", "## 7. Lịch trình")
           .replace("## 8. Team & Roles", "## 8. Đội ngũ / vai trò")
           .replace("## 9. Risk Management", "## 9. Quản lý rủi ro")
           .replace("## 10. Deliverables", "## 10. Sản phẩm bàn giao"))
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"VI sections not recognized: {missing}"


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/D-26.md"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1


if __name__ == "__main__":
    tests = [test_valid_document, test_churn_reported, test_high_churn_flagged,
             test_missing_section, test_no_exit_criteria,
             test_empty_risk_table, test_vietnamese_sections, test_missing_document]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
