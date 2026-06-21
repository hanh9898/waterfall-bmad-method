#!/usr/bin/env python3
"""Tests for check-test-spec-grounding.py (B3-1 / B3-2 / B3-7)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-test-spec-grounding.py")


def _mkdir() -> Path:
    return Path(tempfile.mkdtemp())


def run(d27_path: str, d19: str | None = None, code_dir: str | None = None) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, d27_path]
    if d19:
        cmd += ["--d19", d19]
    if code_dir:
        cmd += ["--code-dir", code_dir]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


# A D-27 whose TCs talk about a model the design declares but code lacks.
D27 = """\
---
document_id: D-27
---

# D-27

## 3. Chi tiết test case (Detailed Test Cases)

### TC-001: Submit tạo snapshot
**REQ ID:** REQ-040
**Facets:** lifecycle, write
**Severity:** Critical
**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | DelM Submit | resource.plan.request state submitted |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| request.state | submitted | |

### TC-002: Idempotent re-sync
**REQ ID:** REQ-041
**Facets:** batch
**Severity:** High
**Test Steps:**

| Step | Action | Expected Result |
|------|--------|----------------|
| 1 | Re-run sync | không nhân đôi |

**Test Data:**

| Input | Value | Notes |
|-------|-------|-------|
| range | 04-06 | |
"""

D19 = """\
---
version: "2.3"
---

# D-19

- **Tên vật lý (Physical name)**: `resource.plan.request`
- **Tên vật lý (Physical name)**: `resource_plan`
"""

CODE_MISSING = "class ResourcePlan(models.Model):\n    _name = 'resource.plan'\n"
CODE_FULL = (
    "class ResourcePlan(models.Model):\n    _name = 'resource.plan'\n\n"
    "class Req(models.Model):\n    _name = 'resource.plan.request'\n"
)


def _write_code(d: Path, body: str) -> str:
    models = d / "models"
    models.mkdir(parents=True)
    (models / "m.py").write_text(body, encoding="utf-8")
    return str(d)


# --- B3-7 model_drift ---

def test_model_drift_design_only_flagged():
    d = _mkdir()
    d27 = d / "D-27.md"; d27.write_text(D27, encoding="utf-8")
    d19 = d / "D-19.md"; d19.write_text(D19, encoding="utf-8")
    code = _write_code(d / "src", CODE_MISSING)
    data, code_rc = run(str(d27), str(d19), code)
    # resource.plan.request declared in D-19 but missing from code → design_only
    assert "resource.plan.request" in data["model_drift"]["design_only"]
    assert data["valid"] is False
    assert code_rc == 1
    assert any(i["type"] == "MODEL_DRIFT_DESIGN_ONLY" for i in data["issues"])


def test_model_drift_clean_when_code_has_model():
    d = _mkdir()
    d27 = d / "D-27.md"; d27.write_text(D27, encoding="utf-8")
    d19 = d / "D-19.md"; d19.write_text(D19, encoding="utf-8")
    code = _write_code(d / "src", CODE_FULL)
    data, _ = run(str(d27), str(d19), code)
    assert data["model_drift"]["design_only"] == []
    assert data["model_drift"]["code_only"] == []


def test_drift_skipped_without_code_dir():
    # B3-7 only runs when BOTH --d19 and --code-dir are given (no half-pair false-green).
    d = _mkdir()
    d27 = d / "D-27.md"; d27.write_text(D27, encoding="utf-8")
    d19 = d / "D-19.md"; d19.write_text(D19, encoding="utf-8")
    data, _ = run(str(d27), str(d19), None)
    assert data["model_drift"]["drift"] is False
    assert data["grounded_code"] is False


# --- B3-2 ungrounded test data ---

def test_ungrounded_testdata_flagged():
    # request.state is not a whole model/field token present in the schema corpus
    # (the schema has resource.plan.request, not request.state).
    d = _mkdir()
    d27 = d / "D-27.md"; d27.write_text(D27, encoding="utf-8")
    d19 = d / "D-19.md"; d19.write_text(D19, encoding="utf-8")
    code = _write_code(d / "src", CODE_FULL)
    data, _ = run(str(d27), str(d19), code)
    assert "request.state" in data["ungrounded_testdata"]


def test_grounded_testdata_not_flagged():
    d = _mkdir()
    d27 = d / "D-27.md"
    d27.write_text(
        "# D-27\n\n## 3. Detail\n\n### TC-001: x\n**REQ ID:** REQ-001\n**Severity:** Low\n\n"
        "**Test Data:**\n\n| Input | Value | Notes |\n|---|---|---|\n| f | resource.plan | |\n",
        encoding="utf-8",
    )
    d19 = d / "D-19.md"; d19.write_text(D19, encoding="utf-8")
    code = _write_code(d / "src", CODE_FULL)
    data, _ = run(str(d27), str(d19), code)
    assert "resource.plan" not in data["ungrounded_testdata"]


def test_testdata_check_skipped_without_schema():
    d = _mkdir()
    d27 = d / "D-27.md"; d27.write_text(D27, encoding="utf-8")
    data, _ = run(str(d27))
    assert data["grounded_schema"] is False
    assert data["ungrounded_testdata"] == []


# --- B3-1 sanity gaps ---

def test_critical_tc_without_sanity_flagged():
    # TC-001 is Critical with no sanity step → flagged.
    d = _mkdir()
    d27 = d / "D-27.md"; d27.write_text(D27, encoding="utf-8")
    data, _ = run(str(d27))
    reqs = {g["req"] for g in data["sanity_gaps"]}
    assert "REQ-040" in reqs  # TC-001 Critical
    assert "REQ-041" in reqs  # TC-002 High + branch 'idempotent'


def test_sanity_step_present_not_flagged():
    d = _mkdir()
    d27 = d / "D-27.md"
    d27.write_text(
        "# D-27\n\n## 3. Detail\n\n### TC-001: x\n**REQ ID:** REQ-040\n**Severity:** Critical\n"
        "**Test Steps:**\n\n| Step | Action | Expected Result |\n|---|---|---|\n"
        "| 0 | Sanity (anti-false-green): snapshot value khác mặc định | fixture phi-mặc-định |\n",
        encoding="utf-8",
    )
    data, _ = run(str(d27))
    assert {g["req"] for g in data["sanity_gaps"]} == set()


def test_medium_branch_tc_not_flagged():
    # A Medium TC merely mentioning a branch word is NOT sensitive (high-signal).
    d = _mkdir()
    d27 = d / "D-27.md"
    d27.write_text(
        "# D-27\n\n## 3. Detail\n\n### TC-001: x\n**REQ ID:** REQ-009\n**Severity:** Medium\n"
        "**Test Steps:**\n\n| Step | Action | Expected Result |\n|---|---|---|\n"
        "| 1 | re-run idempotent | ok |\n",
        encoding="utf-8",
    )
    data, _ = run(str(d27))
    assert {g["req"] for g in data["sanity_gaps"]} == set()


# --- arg / io safety ---

def test_missing_d27_exit_2():
    r = subprocess.run([sys.executable, SCRIPT, "/nope/D-27.md"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2
    assert "error" in json.loads(r.stdout)


def test_missing_d19_is_loud_exit_2():
    d = _mkdir()
    d27 = d / "D-27.md"; d27.write_text(D27, encoding="utf-8")
    r = subprocess.run([sys.executable, SCRIPT, str(d27), "--d19", "/nope/D-19.md"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2
    assert "error" in json.loads(r.stdout)


def test_missing_code_dir_is_loud_exit_2():
    d = _mkdir()
    d27 = d / "D-27.md"; d27.write_text(D27, encoding="utf-8")
    r = subprocess.run([sys.executable, SCRIPT, str(d27), "--code-dir", "/nope/code"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2


def test_honest_verdict_shape():
    d = _mkdir()
    d27 = d / "D-27.md"
    d27.write_text(
        "# D-27\n\n## 3. Detail\n\n### TC-001: x\n**REQ ID:** REQ-001\n**Severity:** Low\n",
        encoding="utf-8",
    )
    data, rc = run(str(d27))
    assert data["structure_ok"] is True
    assert data["semantic_review"] == "n/a"
    assert data["valid"] is True
    assert rc == 0


def test_relative_paths_resolve_via_project_root():
    # absolute-vs-relative: a relative d27 + --project-root must resolve correctly.
    d = _mkdir()
    (d / "D-27.md").write_text(D27, encoding="utf-8")
    r = subprocess.run(
        [sys.executable, SCRIPT, "D-27.md", "--project-root", str(d)],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert r.returncode in (0, 1)  # found + ran (not exit-2 not-found)
    assert "error" not in json.loads(r.stdout)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
