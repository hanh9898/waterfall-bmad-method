#!/usr/bin/env python3
"""Tests for validate-discovery-spike.py (discovery-note)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-discovery-spike.py")

VALID_DOC = """\
---
document_id: discovery-note
feature: "demo"
status: draft
verdict: "VALIDATED"
signed_off_by: "Hanhnt2 (PO)"
---

# Demo — Discovery Note — demo

## 1. Overview
Feature demo có model vòng đời chưa chắc chắn nên cần kiểm chứng rẻ trước.

## 2. Riskiest Assumptions

| ID | Assumption | Why risky | What would falsify it |
|----|------------|-----------|------------------------|
| ASM-01 | Plan stateless sau Submit | Đụng toàn bộ lifecycle | Tìm thấy state machine còn dùng trong code |

## 3. Validation Method

| ASM | Method | Ground-truth checked against |
|-----|--------|-------------------------------|
| ASM-01 | code/DB reality-check | resource/plan.py + bảng resource_plan |

## 4. Evidence
- ASM-01: `resource/plan.py:42` không còn `state` field; xác nhận stateless.

## 5. Verdict

**Verdict:** VALIDATED

**Signed-off-by:** Hanhnt2 (PO), 2026-06-21

## 6. REQ Impact

None

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | 2026-06-21 | Hanhnt2 | Initial discovery spike |
"""


def run_script(doc_content: str) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "discovery-note-demo.md"
        doc_path.write_text(doc_content, encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path), "--project-root", tmpdir]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout), result.returncode


def test_valid_document():
    result, code = run_script(VALID_DOC)
    assert code == 0, f"Expected 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["semantic_review"] == "n/a"
    assert result["passed"] is True
    assert result["verdict_value"] == "VALIDATED"
    assert result["assumption_count"] == 1


def test_missing_section():
    doc = VALID_DOC.replace("## 4. Evidence", "## 4. Removed")
    result, code = run_script(doc)
    assert code == 1
    assert any(i["type"] == "SECTION_MISSING" for i in result["issues"])


def test_no_assumption():
    doc = VALID_DOC.replace("| ASM-01 | Plan stateless sau Submit", "| XX-01 | Plan stateless sau Submit")
    result, code = run_script(doc)
    assert any(i["type"] == "NO_ASSUMPTION" for i in result["issues"])


def test_invalid_verdict():
    doc = VALID_DOC.replace("**Verdict:** VALIDATED", "**Verdict:** MAYBE")
    result, code = run_script(doc)
    assert any(i["type"] == "INVALID_VERDICT" for i in result["issues"])


def test_signoff_missing():
    doc = VALID_DOC.replace("**Signed-off-by:** Hanhnt2 (PO), 2026-06-21", "**Signed-off-by:**")
    result, code = run_script(doc)
    assert any(i["type"] == "SIGNOFF_MISSING" for i in result["issues"])


def test_reshape_requires_req_impact():
    doc = VALID_DOC.replace("**Verdict:** VALIDATED", "**Verdict:** RESHAPE")
    result, code = run_script(doc)
    assert any(i["type"] == "REQ_IMPACT_MISSING" for i in result["issues"])


def test_reshape_with_req_impact_ok():
    doc = (VALID_DOC
           .replace("**Verdict:** VALIDATED", "**Verdict:** RESHAPE")
           .replace("## 6. REQ Impact\n\nNone",
                    "## 6. REQ Impact\n\nREQ-DEMO-001 phải sửa lại: bỏ giả định stateless."))
    result, code = run_script(doc)
    assert code == 0, f"Expected 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["verdict_value"] == "RESHAPE"


def test_vietnamese_sections():
    doc = (VALID_DOC
           .replace("## 1. Overview", "## 1. Tổng quan")
           .replace("## 2. Riskiest Assumptions", "## 2. Giả định rủi ro nhất")
           .replace("## 3. Validation Method", "## 3. Phương pháp kiểm chứng")
           .replace("## 4. Evidence", "## 4. Bằng chứng")
           .replace("## 5. Verdict", "## 5. Kết luận")
           .replace("## Revision History", "## Lịch sử sửa đổi"))
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"VI sections not recognized: {missing}"


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/discovery-note.md", "--project-root", "/tmp"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1


if __name__ == "__main__":
    tests = [test_valid_document, test_missing_section, test_no_assumption,
             test_invalid_verdict, test_signoff_missing, test_reshape_requires_req_impact,
             test_reshape_with_req_impact_ok, test_vietnamese_sections, test_missing_document]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
