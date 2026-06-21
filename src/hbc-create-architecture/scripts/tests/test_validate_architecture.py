#!/usr/bin/env python3
"""Tests for validate-architecture.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-architecture.py")

VALID_DOC = """\
---
document_id: D-08
feature: "demo"
version: "1.0"
status: draft
---

# Demo — Architecture Design

## Overview

Kiến trúc cho feature demo. Driver chính: NFR hiệu năng p95 < 2s và tích hợp module thanh toán.

## Components

| Component | Responsibility | Layer | REQ Ref |
|-----------|----------------|-------|---------|
| OrderService | Điều phối tạo đơn | service | REQ-DEMO-001 |
| OrderModel | Lưu trạng thái đơn | model | REQ-DEMO-002 |

## Integration Points

| Integration Point | Existing System Ref | Change Type | Contract / Seam |
|-------------------|---------------------|-------------|-----------------|
| Payment | module:payment | CHANGE | gọi charge() đồng bộ |

## NFR-Driven Decisions

| NFR Ref | Structural choice | ADR |
|---------|-------------------|-----|
| NFR-PERF-001 | read-model cache | ADR-01 |

## Decision Records

### ADR-01: Read-model cache cho danh sách đơn

- **Decision:** Dùng read-model cache cho màn hình danh sách.
- **Rationale:** NFR-PERF-001 yêu cầu p95 < 2s; query trực tiếp không đạt.
- **Alternatives considered:** Index thuần (không đủ), denormalize cột (rủi ro nhất quán).
- **REQ / NFR Ref:** REQ-DEMO-001 / NFR-PERF-001

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | 2026-06-21 | Test | Bản đầu |
"""


def run_script(doc_content: str) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-08-demo-architecture.md"
        doc_path.write_text(doc_content, encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path), "--project-root", tmpdir]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout), result.returncode


def test_valid_document():
    result, code = run_script(VALID_DOC)
    assert code == 0, f"Expected 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["structure_ok"] is True
    assert result["semantic_review"] == "n/a"
    assert result["adr_count"] == 1
    assert result["passed"] is True


def test_missing_section():
    doc = VALID_DOC.replace("## Integration Points", "## Removed Section")
    result, code = run_script(doc)
    assert code == 1
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert any(i["section"] == "Integration Points" for i in missing)


def test_empty_section():
    doc = VALID_DOC.replace(
        "Kiến trúc cho feature demo. Driver chính: NFR hiệu năng p95 < 2s và tích hợp module thanh toán.",
        "",
    )
    result, code = run_script(doc)
    empty = [i for i in result["issues"] if i["type"] == "SECTION_EMPTY"]
    assert any(i["section"] == "Overview" for i in empty)


def test_no_req_ref():
    doc = VALID_DOC.replace("REQ-DEMO-001", "X").replace("REQ-DEMO-002", "Y")
    result, code = run_script(doc)
    assert any(i["type"] == "NO_REQ_REF" for i in result["issues"])


def test_adr_without_rationale():
    doc = VALID_DOC.replace(
        "- **Rationale:** NFR-PERF-001 yêu cầu p95 < 2s; query trực tiếp không đạt.\n",
        "",
    )
    result, code = run_script(doc)
    assert any(i["type"] == "ADR_NO_RATIONALE" for i in result["issues"])


def test_vietnamese_sections_recognized():
    doc = (VALID_DOC
           .replace("## Overview", "## Tổng quan")
           .replace("## Components", "## Thành phần")
           .replace("## Integration Points", "## Điểm tích hợp")
           .replace("## Decision Records", "## Bản ghi quyết định")
           .replace("## Revision History", "## Lịch sử sửa đổi"))
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"VI sections not recognized: {missing}"


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/D-08.md", "--project-root", "/tmp"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1
    assert "error" in json.loads(result.stdout)


if __name__ == "__main__":
    tests = [
        test_valid_document,
        test_missing_section,
        test_empty_section,
        test_no_req_ref,
        test_adr_without_rationale,
        test_vietnamese_sections_recognized,
        test_missing_document,
    ]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
