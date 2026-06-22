#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for cascade-precheck.py (B7-1/B7-3/B7-5/B7-6). Run via pytest or `python test_cascade_precheck.py`."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "cascade-precheck.py"
# The frozen TD.0 broken fixture (the RCA error state).
FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "process-review" / "fixtures" / "resource-plan-billable"
)
FIX_ART = FIXTURE / "artifacts"

# A clean matrix: D-02 defines REQ-001/002, matrix traces both fully.
D02_CLEAN = (
    "## Yêu cầu chức năng (Functional Requirements)\n\n"
    "| REQ ID | Mô tả |\n|---|---|\n"
    "| REQ-AUTH-001 | Login |\n| REQ-AUTH-002 | Lockout |\n"
)
MATRIX_CLEAN = (
    "| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
    "|---|---|---|---|---|---|---|---|\n"
    "| auth | REQ-AUTH-001 | | Entity_User | auth.py:login | TC-001 | | 2026-01-01 |\n"
    "| auth | REQ-AUTH-002 | | Entity_User | auth.py:lock | TC-002 | | 2026-01-01 |\n"
)


def run(*args, expect_code=None):
    p = subprocess.run([sys.executable, str(SCRIPT), *args],
                       capture_output=True, text=True, encoding="utf-8")
    if expect_code is not None:
        assert p.returncode == expect_code, f"exit {p.returncode} != {expect_code}\n{p.stdout}\n{p.stderr}"
    data = json.loads(p.stdout) if p.stdout.strip() else {"error": p.stderr}
    return data, p.returncode


def test_clean_matrix_passes(tmp_path):
    d02 = tmp_path / "D-02.md"; d02.write_text(D02_CLEAN, encoding="utf-8")
    mx = tmp_path / "matrix.md"; mx.write_text(MATRIX_CLEAN, encoding="utf-8")
    data, code = run("--d02", str(d02), "--matrix", str(mx), expect_code=0)
    assert data["blocked"] is False, data
    assert data["reason"] is None
    assert data["missing_from_matrix"] == []
    assert data["coverage_gaps"] == {}


def test_missing_row_blocks_untraced_change(tmp_path):
    # B7-6 + B7-1: D-02 has REQ-002 but the matrix never received its row → BLOCK.
    d02 = tmp_path / "D-02.md"; d02.write_text(D02_CLEAN, encoding="utf-8")
    mx = tmp_path / "matrix.md"
    mx.write_text(
        "| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| auth | REQ-AUTH-001 | | E | c | TC-001 | | t |\n",
        encoding="utf-8",
    )
    data, code = run("--d02", str(d02), "--matrix", str(mx), expect_code=1)
    assert data["blocked"] is True
    assert data["reason"] == "untraced_change"
    assert data["cascade_required"] is True
    assert "REQ-AUTH-002" in data["missing_from_matrix"]


def test_blank_column_blocks(tmp_path):
    # B7-6: row exists but code_ref is blank → untraced for that axis → BLOCK.
    d02 = tmp_path / "D-02.md"; d02.write_text(D02_CLEAN, encoding="utf-8")
    mx = tmp_path / "matrix.md"
    mx.write_text(
        "| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| auth | REQ-AUTH-001 | | E | c | TC-001 | | t |\n"
        "| auth | REQ-AUTH-002 | | E |  | TC-002 | | t |\n",
        encoding="utf-8",
    )
    data, code = run("--d02", str(d02), "--matrix", str(mx), expect_code=1)
    assert data["blocked"] is True
    assert "REQ-AUTH-002" in data["coverage_gaps"]
    assert "code_ref" in data["coverage_gaps"]["REQ-AUTH-002"]


def test_drift_watch_warns(tmp_path):
    # B7-3: a task-breakdown citing D-02 v1.8 while D-02 is v2.3 → drift_watch warning.
    d02 = tmp_path / "D-02.md"
    d02.write_text("---\nversion: \"2.3\"\n---\n" + D02_CLEAN, encoding="utf-8")
    mx = tmp_path / "matrix.md"; mx.write_text(MATRIX_CLEAN, encoding="utf-8")
    tb = tmp_path / "tb.md"; tb.write_text("sources:\n  - D-02 v1.8 (39 REQ)\n", encoding="utf-8")
    # Clean matrix → not blocked, but warning present. Default exit 0 (warnings non-blocking).
    data, code = run("--d02", str(d02), "--matrix", str(mx), "--task-breakdown", str(tb), expect_code=0)
    assert data["blocked"] is False
    assert any(d["cited"] == "1.8" and d["declared"] == "2.3" for d in data["drift_watch"]), data["drift_watch"]


def test_strict_exits_1_on_warning_only(tmp_path):
    # A5: --strict stops for a human even when only a (non-blocking) warning exists.
    d02 = tmp_path / "D-02.md"
    d02.write_text("---\nversion: \"2.3\"\n---\n" + D02_CLEAN, encoding="utf-8")
    mx = tmp_path / "matrix.md"; mx.write_text(MATRIX_CLEAN, encoding="utf-8")
    tb = tmp_path / "tb.md"; tb.write_text("sources:\n  - D-02 v1.8\n", encoding="utf-8")
    _, code = run("--d02", str(d02), "--matrix", str(mx), "--task-breakdown", str(tb), "--strict")
    assert code == 1


def test_no_matrix_table_blocks(tmp_path):
    # Silent-green guard: matrix mentions REQ ids but no parseable table → BLOCK.
    d02 = tmp_path / "D-02.md"; d02.write_text(D02_CLEAN, encoding="utf-8")
    mx = tmp_path / "matrix.md"
    mx.write_text("Some prose mentioning REQ-AUTH-001 but no table.\n", encoding="utf-8")
    data, code = run("--d02", str(d02), "--matrix", str(mx), expect_code=1)
    assert data["blocked"] is True
    assert any(b["type"] == "NO_MATRIX_TABLE" for b in data["blockers"]), data["blockers"]


def test_td0_broken_fixture_blocks():
    """The cardinal proof: on the frozen TD.0 broken fixture the engine BLOCKS —
    it must NOT report a clean/complete matrix (missing 040/041/042 + stale citations)."""
    if not FIXTURE.exists():
        import pytest
        pytest.skip("TD.0 fixture not present")
    d02 = FIX_ART / "planning-artifacts" / "D-02-resource-plan-billable.md"
    mx = FIX_ART / "traceability" / "matrix.md"
    d27 = FIX_ART / "planning-artifacts" / "D-27-resource-plan-billable-test-spec.md"
    tb = FIX_ART / "implementation-artifacts" / "task-breakdown.md"
    design = FIX_ART / "planning-artifacts" / "D-19-opms" / "D-19-er-diagram.md"
    data, code = run(
        "--d02", str(d02), "--matrix", str(mx), "--d27", str(d27),
        "--task-breakdown", str(tb),
        "--gate-reports-glob", str(FIX_ART / "gates" / "phase-*-gate.md"),
        "--design", str(design), "--code-dir", str(FIXTURE / "code"),
        expect_code=1,
    )
    assert data["blocked"] is True, data
    assert data["reason"] == "untraced_change"
    assert data["cascade_required"] is True
    # missing rows 040/041/042 surfaced (trailing-number identity → canonical ids)
    missing_nums = {m.rsplit("-", 1)[-1] for m in data["missing_from_matrix"]}
    assert {"040", "041", "042"} <= missing_nums, data["missing_from_matrix"]
    # B7-3 drift-watch flags the stale D-02 v1.8/2.2 citations
    assert any(d["cited"] != "2.3" for d in data["drift_watch"]), data["drift_watch"]
    # B7-5 structural-route fires (request/snapshot models absent from code)
    assert data["structural_route"], data["structural_route"]


if __name__ == "__main__":
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    test_clean_matrix_passes(tmp)
    test_missing_row_blocks_untraced_change(tmp)
    test_blank_column_blocks(tmp)
    test_drift_watch_warns(tmp)
    test_strict_exits_1_on_warning_only(tmp)
    test_no_matrix_table_blocks(tmp)
    test_td0_broken_fixture_blocks()
    print("ALL PASS")
