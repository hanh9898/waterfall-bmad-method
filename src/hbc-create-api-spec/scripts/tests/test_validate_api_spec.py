#!/usr/bin/env python3
"""Tests for validate-api-spec.py (D-21)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-api-spec.py")

VALID_DOC = """\
---
document_id: D-21
feature: "demo"
version: "1.0"
status: draft
---

# Demo — API Specification

## 1. Overview
API cho feature demo.

## 2. Authentication
Bearer token (JWT).

## 3. Common Specifications
JSON request/response, UTF-8, mã lỗi chuẩn.

## 4. Endpoint List

| # | Method | Endpoint | Description | REQ |
|---|--------|----------|-------------|-----|
| 1 | GET | /orders | Lấy danh sách đơn | REQ-DEMO-001 |
| 2 | POST | /orders | Tạo đơn mới | REQ-DEMO-002 |

## 5. Endpoint Details

### GET /orders
Trả về danh sách đơn. REQ-DEMO-001.

### POST /orders
Tạo đơn. REQ-DEMO-002.

## 6. Data Models

### Order
- id: int
- state: str
"""


def run_script(doc_content: str) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-21-demo.md"
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
    doc = VALID_DOC.replace("## 6. Data Models", "## 6. Removed")
    result, code = run_script(doc)
    assert code == 1
    assert any(i["type"] == "SECTION_MISSING" for i in result["issues"])


def test_invalid_method():
    doc = VALID_DOC.replace("| 1 | GET | /orders", "| 1 | FETCH | /orders")
    result, code = run_script(doc)
    assert any(i["type"] == "INVALID_METHOD" for i in result["issues"])


def test_no_req_reference():
    doc = VALID_DOC.replace("Lấy danh sách đơn | REQ-DEMO-001", "Lấy danh sách đơn | ")
    result, code = run_script(doc)
    assert any(i["type"] == "NO_REQ_REFERENCE" for i in result["issues"])


def test_vietnamese_sections():
    doc = (VALID_DOC
           .replace("## 1. Overview", "## 1. Tổng quan")
           .replace("## 2. Authentication", "## 2. Xác thực")
           .replace("## 3. Common Specifications", "## 3. Quy cách chung")
           .replace("## 4. Endpoint List", "## 4. Danh sách endpoint")
           .replace("## 5. Endpoint Details", "## 5. Chi tiết endpoint")
           .replace("## 6. Data Models", "## 6. Mô hình dữ liệu"))
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"VI sections not recognized: {missing}"


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/D-21.md"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1


if __name__ == "__main__":
    tests = [test_valid_document, test_missing_section, test_invalid_method,
             test_no_req_reference, test_vietnamese_sections, test_missing_document]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
