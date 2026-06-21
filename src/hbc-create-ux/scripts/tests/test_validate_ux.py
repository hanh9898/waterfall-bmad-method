#!/usr/bin/env python3
"""Tests for validate-ux.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-ux.py")

VALID_DOC = """\
---
document_id: D-14
feature: "demo"
version: "1.0"
status: draft
uses_claude_design: false
---

# Demo — UX / Screen Design

## Overview

Thiết kế UX cho REQ-DEMO-001 (màn danh sách đơn). Token tham chiếu DESIGN.md; không dùng Claude Design.

## Screens

| ID | Screen | REQ Ref | D-06 Path | Mockup Ref |
|----|--------|---------|-----------|------------|
| SCR-01 | Danh sách đơn | REQ-DEMO-001 | path:list-orders | — |

## Components

| ID | Component | Screen | Visual tokens | REQ Ref |
|----|-----------|--------|---------------|---------|
| CMP-01 | OrderTable | SCR-01 | {color.primary}, {spacing.md} | REQ-DEMO-001 |

## States & Interactions

| Component | State | Appearance / Behaviour |
|-----------|-------|------------------------|
| CMP-01 | default | hiện danh sách |
| CMP-01 | empty | hiện thông báo trống |

## Traceability

| REQ Ref | Screen | Component(s) | Test Ref (E2E / UI) |
|---------|--------|--------------|---------------------|
| REQ-DEMO-001 | SCR-01 | CMP-01 | E2E-DEMO-001 |

## UI Acceptance & Visual Regression

| Screen | Acceptance criteria | Visual-regression baseline | Method (consumer tool) |
|--------|---------------------|----------------------------|------------------------|
| SCR-01 | danh sách hiển thị đúng | N/A | Playwright snapshot |

## Dev Notes

Phân trang server-side.

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | 2026-06-21 | Test | Bản đầu |
"""


def run_script(doc_content: str) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-14-demo-ux.md"
        doc_path.write_text(doc_content, encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path), "--project-root", tmpdir]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout), result.returncode


def test_valid_document():
    result, code = run_script(VALID_DOC)
    assert code == 0, f"Expected 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["screen_count"] == 1
    assert result["component_count"] == 1
    assert result["advisory_count"] == 0
    assert result["passed"] is True
    assert result["churn"]["high_churn"] is False


def test_no_screen():
    doc = VALID_DOC.replace("SCR-01", "X-01")
    result, code = run_script(doc)
    assert code == 1
    assert any(i["type"] == "NO_SCREEN" for i in result["issues"])


def test_duplicate_element_id():
    # two CMP-01 DEFINITION rows in the Components table = real duplicate
    doc = VALID_DOC.replace(
        "| CMP-01 | OrderTable | SCR-01 | {color.primary}, {spacing.md} | REQ-DEMO-001 |",
        "| CMP-01 | OrderTable | SCR-01 | {color.primary}, {spacing.md} | REQ-DEMO-001 |\n"
        "| CMP-01 | Dup | SCR-01 | {color.primary} | REQ-DEMO-001 |",
    )
    result, code = run_script(doc)
    assert any(i["type"] == "DUPLICATE_ELEMENT_ID" for i in result["issues"])


def test_no_req_ref():
    doc = VALID_DOC.replace("REQ-DEMO-001", "x")
    result, code = run_script(doc)
    assert any(i["type"] == "NO_REQ_REF" for i in result["issues"])


def test_missing_section():
    doc = VALID_DOC.replace("## Screens", "## Removed")
    result, code = run_script(doc)
    assert any(i["type"] == "SECTION_MISSING" and i["section"] == "Screens"
               for i in result["issues"])


def test_inline_visual_advisory_non_blocking():
    doc = VALID_DOC.replace("{color.primary}, {spacing.md}", "#ff0000, 12px")
    result, code = run_script(doc)
    # advisory present but does NOT fail validity
    assert result["advisory_count"] >= 1
    assert any(a["type"] == "INLINE_VISUAL_VALUE" for a in result["advisories"])
    assert result["valid"] is True
    assert code == 0


def test_vietnamese_sections():
    doc = (VALID_DOC
           .replace("## Overview", "## Tổng quan")
           .replace("## Screens", "## Màn hình")
           .replace("## Components", "## Thành phần")
           .replace("## Traceability", "## Truy vết")
           .replace("## Revision History", "## Lịch sử sửa đổi"))
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"VI sections not recognized: {missing}"


def test_high_churn_flag():
    # 5 dated revision rows > threshold 4 → high_churn true (T2.11)
    extra = "\n".join(f"| 1.{n} | 2026-06-2{n} | Test | edit {n} |" for n in range(1, 6))
    doc = VALID_DOC.replace(
        "| 1.0 | 2026-06-21 | Test | Bản đầu |",
        "| 1.0 | 2026-06-21 | Test | Bản đầu |\n" + extra,
    )
    result, code = run_script(doc)
    assert result["churn"]["high_churn"] is True
    assert result["churn"]["revisions"] >= 5


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/D-14.md", "--project-root", "/tmp"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1
    assert "error" in json.loads(result.stdout)


if __name__ == "__main__":
    tests = [
        test_valid_document, test_no_screen, test_duplicate_element_id, test_no_req_ref,
        test_missing_section, test_inline_visual_advisory_non_blocking,
        test_vietnamese_sections, test_high_churn_flag, test_missing_document,
    ]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
