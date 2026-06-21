#!/usr/bin/env python3
"""Tests for validate-behavioral-design.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-behavioral-design.py")

VALID_DOC = """\
---
document_id: D-17
feature: "demo"
version: "1.0"
status: draft
---

# Demo — Behavioral Design

## Overview

REQ-DEMO-001 là một state-machine (has-state-machine); REQ-DEMO-002 có invariant immutability.

## REQ-DEMO-001: Vòng đời đơn

### State Transitions

| ID | From | Event | Guard | To |
|----|------|-------|-------|-----|
| ST-01 | draft | submit | có ≥1 dòng | submitted |
| ST-02 | submitted | submit | — | (illegal) |

### Sequence / Interaction

| ID | Step |
|----|------|
| SEQ-01 | Khi submit → snapshot dòng đơn trước khi đổi trạng thái |

## REQ-DEMO-002: Bất biến snapshot

### Invariants

| ID | Invariant | Enforcement point |
|----|-----------|-------------------|
| INV-01 | snapshot không đổi sau submit | model write guard |

### Decision Table

| ID | Conditions | Action |
|----|-----------|--------|
| DR-01 | trạng thái = submitted | chặn sửa dòng |

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | 2026-06-21 | Test | Bản đầu |
"""


def run_script(doc_content: str) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-17-demo-behavioral-design.md"
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


def test_element_count_counts_unique():
    result, _ = run_script(VALID_DOC)
    # ST-01, ST-02, SEQ-01, INV-01, DR-01 = 5 unique element ids
    assert result["element_count"] == 5


def test_no_behavior_element():
    doc = VALID_DOC
    for eid in ["ST-01", "ST-02", "SEQ-01", "INV-01", "DR-01"]:
        doc = doc.replace(eid, "XX")
    result, code = run_script(doc)
    assert code == 1
    assert any(i["type"] == "NO_BEHAVIOR_ELEMENT" for i in result["issues"])


def test_duplicate_element_id():
    doc = VALID_DOC.replace("| INV-01 | snapshot không đổi sau submit | model write guard |",
                            "| ST-01 | snapshot không đổi sau submit | model write guard |")
    result, code = run_script(doc)
    assert any(i["type"] == "DUPLICATE_ELEMENT_ID" for i in result["issues"])


def test_no_req_ref():
    doc = VALID_DOC.replace("REQ-DEMO-001", "x").replace("REQ-DEMO-002", "y")
    result, code = run_script(doc)
    assert any(i["type"] == "NO_REQ_REF" for i in result["issues"])


def test_missing_section():
    doc = VALID_DOC.replace("## Revision History", "## Removed")
    result, code = run_script(doc)
    assert any(i["type"] == "SECTION_MISSING" and i["section"] == "Revision History"
               for i in result["issues"])


def test_vietnamese_sections():
    doc = VALID_DOC.replace("## Overview", "## Tổng quan").replace("## Revision History", "## Lịch sử sửa đổi")
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"VI sections not recognized: {missing}"


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/D-17.md", "--project-root", "/tmp"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1
    assert "error" in json.loads(result.stdout)


if __name__ == "__main__":
    tests = [
        test_valid_document, test_element_count_counts_unique, test_no_behavior_element,
        test_duplicate_element_id, test_no_req_ref, test_missing_section,
        test_vietnamese_sections, test_missing_document,
    ]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
