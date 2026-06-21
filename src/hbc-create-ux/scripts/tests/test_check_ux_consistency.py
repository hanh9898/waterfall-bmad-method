#!/usr/bin/env python3
"""Tests for check-ux-consistency.py (advisory UX-2/3/4/6/7 checks)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-ux-consistency.py")

# A clean D-14: every REQ has a screen, screen has component + test, component has
# a token, no Claude Design (so mockup/token-source checks are off).
CLEAN = """\
---
document_id: D-14
feature: "demo"
uses_claude_design: false
design_token_source: ""
---

# Demo — UX / Screen Design

## Overview
Thiết kế UX cho REQ-DEMO-001.

## Screens

| ID | Screen | REQ Ref | D-06 Path | Mockup Ref |
|----|--------|---------|-----------|------------|
| SCR-01 | Danh sách | REQ-DEMO-001 | path:list | — |

## Components

| ID | Component | Screen | Visual tokens | Code Ref | REQ Ref |
|----|-----------|--------|---------------|----------|---------|
| CMP-01 | OrderTable | SCR-01 | {color.primary} | — | REQ-DEMO-001 |

## States & Interactions

| Component | State | Behaviour |
|-----------|-------|-----------|
| CMP-01 | default | hiện |

## Traceability

| REQ Ref | Screen | Component(s) | Test Ref (E2E / UI) |
|---------|--------|--------------|---------------------|
| REQ-DEMO-001 | SCR-01 | CMP-01 | E2E-DEMO-001 |

## Revision History

| Version | Date | Author | Scope |
|---------|------|--------|-------|
| 1.0 | 2026-06-21 | T | init |
"""


def run_script(doc_content: str, extra_args=None, code_dir=None) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-14-demo-ux.md"
        doc_path.write_text(doc_content, encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path), "--project-root", tmpdir]
        if extra_args:
            cmd += extra_args
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout), result.returncode


def _types(result):
    return {a["type"] for a in result.get("advisories", [])}


def test_clean_doc_passes():
    result, code = run_script(CLEAN)
    assert code == 0, result
    assert result["valid"] is True
    assert result["advisory"] is True
    assert result["advisory_count"] == 0
    assert result["screen_count"] == 1
    assert result["component_count"] == 1


def test_req_no_screen():
    # add a REQ in prose that no screen serves
    doc = CLEAN.replace("Thiết kế UX cho REQ-DEMO-001.",
                        "Thiết kế UX cho REQ-DEMO-001 và REQ-DEMO-009.")
    result, code = run_script(doc)
    assert code == 1
    assert "REQ_NO_SCREEN" in _types(result)
    assert any(a.get("req") == "REQ-DEMO-009" for a in result["advisories"])


def test_screen_no_test():
    doc = CLEAN.replace("| REQ-DEMO-001 | SCR-01 | CMP-01 | E2E-DEMO-001 |",
                        "| REQ-DEMO-001 | SCR-01 | CMP-01 | — |")
    result, code = run_script(doc)
    assert "SCREEN_NO_TEST" in _types(result)


def test_screen_no_component():
    # component maps to a different screen → SCR-01 has no component
    doc = CLEAN.replace("| CMP-01 | OrderTable | SCR-01 |",
                        "| CMP-01 | OrderTable | SCR-99 |")
    result, code = run_script(doc)
    assert "SCREEN_NO_COMPONENT" in _types(result)


def test_component_no_token():
    doc = CLEAN.replace("| CMP-01 | OrderTable | SCR-01 | {color.primary} | — | REQ-DEMO-001 |",
                        "| CMP-01 | OrderTable | SCR-01 |  | — | REQ-DEMO-001 |")
    result, code = run_script(doc)
    assert "COMPONENT_NO_TOKEN" in _types(result)


def test_claude_design_mockup_and_token_source():
    # uses_claude_design true, mockup blank + no token source → both fire
    doc = (CLEAN
           .replace("uses_claude_design: false", "uses_claude_design: true"))
    result, code = run_script(doc)
    types = _types(result)
    assert "MOCKUP_MISSING" in types
    assert "TOKEN_SOURCE_MISSING" in types
    assert result["uses_claude_design"] is True


def test_claude_design_quoted_boolean():
    # a YAML-valid quoted boolean must still enable the checks (no false-green)
    doc = CLEAN.replace('uses_claude_design: false', 'uses_claude_design: "true"')
    result, code = run_script(doc)
    assert result["uses_claude_design"] is True
    assert "MOCKUP_MISSING" in _types(result)


def test_claude_design_flag_override():
    # frontmatter says false; --uses-claude-design forces the checks on
    result, code = run_script(CLEAN, extra_args=["--uses-claude-design"])
    assert "MOCKUP_MISSING" in _types(result)
    assert result["uses_claude_design"] is True


def test_code_reconcile_missing_symbol():
    doc = CLEAN.replace("| CMP-01 | OrderTable | SCR-01 | {color.primary} | — | REQ-DEMO-001 |",
                        "| CMP-01 | OrderTable | SCR-01 | {color.primary} | `OrderTable` | REQ-DEMO-001 |")
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-14-demo-ux.md"
        doc_path.write_text(doc, encoding="utf-8")
        code_dir = Path(tmpdir) / "code"
        code_dir.mkdir()
        (code_dir / "views.js").write_text("const SomethingElse = 1;\n", encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path), "--project-root", tmpdir,
               "--code-dir", str(code_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        out = json.loads(result.stdout)
    assert out["code_reconciled"] is True
    assert "COMPONENT_NOT_IN_CODE" in {a["type"] for a in out["advisories"]}


def test_code_reconcile_symbol_present():
    doc = CLEAN.replace("| CMP-01 | OrderTable | SCR-01 | {color.primary} | — | REQ-DEMO-001 |",
                        "| CMP-01 | OrderTable | SCR-01 | {color.primary} | `OrderTable` | REQ-DEMO-001 |")
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-14-demo-ux.md"
        doc_path.write_text(doc, encoding="utf-8")
        code_dir = Path(tmpdir) / "code"
        code_dir.mkdir()
        (code_dir / "views.js").write_text("class OrderTable {}\n", encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path), "--project-root", tmpdir,
               "--code-dir", str(code_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        out = json.loads(result.stdout)
    assert "COMPONENT_NOT_IN_CODE" not in {a["type"] for a in out["advisories"]}


def test_missing_code_dir_is_loud_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-14-demo-ux.md"
        doc_path.write_text(CLEAN, encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path), "--project-root", tmpdir,
               "--code-dir", str(Path(tmpdir) / "nope")]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        assert result.returncode == 2
        assert "error" in json.loads(result.stdout)


def test_vietnamese_sections():
    doc = (CLEAN
           .replace("## Screens", "## Màn hình")
           .replace("## Components", "## Thành phần")
           .replace("## Traceability", "## Truy vết"))
    result, code = run_script(doc)
    # still clean — VI labels are recognized, so no spurious gaps
    assert result["advisory_count"] == 0, result["advisories"]


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/D-14.md", "--project-root", "/tmp"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 2
    assert "error" in json.loads(result.stdout)


if __name__ == "__main__":
    tests = [
        test_clean_doc_passes, test_req_no_screen, test_screen_no_test,
        test_screen_no_component, test_component_no_token,
        test_claude_design_mockup_and_token_source, test_claude_design_quoted_boolean,
        test_claude_design_flag_override,
        test_code_reconcile_missing_symbol, test_code_reconcile_symbol_present,
        test_missing_code_dir_is_loud_error, test_vietnamese_sections,
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
