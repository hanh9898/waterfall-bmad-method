"""Tests for validate-constitution.py — invoked via subprocess like SKILL.md."""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "validate-constitution.py"
TEMPLATE = Path(__file__).resolve().parents[2] / "assets" / "constitution_template.md"


def run(path, expect_rc=0, **kw):
    cmd = [sys.executable, str(SCRIPT), str(path)]
    for k, v in kw.items():
        cmd += [f"--{k.replace('_', '-')}", str(v)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == expect_rc, proc.stderr
    if expect_rc == 0:
        return json.loads(proc.stdout)
    return proc


FULL = """---
title: "X Constitution"
version: "1.0"
lastStep: complete
semanticReview:
  status: passed
  openFacets: []
---
# Project Constitution

## 1. Test-First (TDD)
Every behavior change is driven by a failing test first.

## 2. Language Policy
Source English; output configured language.

## 3. Separation of Duties (SoD)
Each phase has an owner persona.

## 4. Handoff Through Artifact
Phases communicate through committed artifacts.

## 5. Simplicity Caps
Default to the simplest thing.
"""


def test_full_passes(tmp_path):
    p = tmp_path / "constitution.md"
    p.write_text(FULL, encoding="utf-8")
    r = run(p)
    assert r["issues"] == []
    assert r["verdict"]["structure_ok"] is True
    assert r["verdict"]["passed"] is True
    assert r["semantic_review"]["passed"] is True


def test_missing_principle(tmp_path):
    p = tmp_path / "constitution.md"
    p.write_text(FULL.replace("## 5. Simplicity Caps\nDefault to the simplest thing.", ""),
                 encoding="utf-8")
    r = run(p)
    sections = {i["section"] for i in r["issues"]}
    assert "Simplicity Caps" in sections
    assert r["verdict"]["structure_ok"] is False


def test_clarification_marker_blocks(tmp_path):
    p = tmp_path / "constitution.md"
    p.write_text(FULL.replace("Default to the simplest thing.",
                              "[NEEDS CLARIFICATION: caps?]"), encoding="utf-8")
    r = run(p)
    assert r["clarification_markers"] >= 1
    assert r["verdict"]["structure_ok"] is False


def test_pending_when_review_not_passed(tmp_path):
    p = tmp_path / "constitution.md"
    p.write_text(FULL.replace("status: passed", "status: pending"), encoding="utf-8")
    r = run(p)
    # structure ok but semantic pending -> verdict not passed
    assert r["verdict"]["structure_ok"] is True
    assert r["verdict"]["passed"] is False
    assert r["semantic_review"]["passed"] is False


def test_template_validates_structurally(tmp_path):
    # The shipped template has the 5 principles but carries [NEEDS CLARIFICATION]
    # placeholders and pending review by design -> structure_ok False until filled.
    r = run(TEMPLATE)
    sections = {i["section"] for i in r["issues"]}
    # all 5 principle headings present (none missing/empty)
    assert "Test-First" not in sections
    assert "Simplicity Caps" not in sections
    # but unresolved clarification markers are flagged
    assert r["clarification_markers"] >= 1


def test_missing_file(tmp_path):
    run(tmp_path / "nope.md", expect_rc=2)
