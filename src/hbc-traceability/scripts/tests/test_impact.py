#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for impact.py (detect / analyze / freeze / complete). Run via pytest or `python test_impact.py`."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "impact.py"

MATRIX = """\
| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |
|--------|----------|------------|----------|----------|-------------|-----------|
| REQ-010 |  | Customer.credit_limit | customer.py:set_limit | TC-101 |  | 2026-01-01 |
| REQ-022 |  | Customer.credit_limit, Order | order.py:check | TC-220 |  | 2026-01-01 |
| REQ-030 |  | Invoice | invoice.py | TC-300 | PASSED | 2026-01-01 |
"""


def run(*args, expect_code=0):
    p = subprocess.run([sys.executable, str(SCRIPT), *args],
                       capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == expect_code, f"exit {p.returncode} != {expect_code}\n{p.stdout}\n{p.stderr}"
    return json.loads(p.stdout) if p.stdout.strip() else {}


def _matrix(tmp_path):
    mx = tmp_path / "matrix.md"
    mx.write_text(MATRIX, encoding="utf-8")
    return mx


def test_freeze_task_tier_done(tmp_path):
    # Bug H1: a DONE task whose refs match a REQ's matrix refs must freeze it via
    # the task tier. The old space-join + ',;'-only split collapsed the three ref
    # columns into one token that never matched a task blob, so the tier never fired.
    mx = _matrix(tmp_path)
    tb = tmp_path / "task-breakdown.md"
    tb.write_text(
        "| task_id | description | design_ref | test_refs | priority | status | dependencies |\n"
        "|---------|-------------|------------|-----------|----------|--------|--------------|\n"
        "| TASK-001 | Credit limit | Customer.credit_limit | TC-101 | High | DONE | - |\n",
        encoding="utf-8",
    )
    r = run("freeze", "--matrix", str(mx), "--reqs", "REQ-010",
            "--task-breakdown", str(tb), "--project-root", str(tmp_path))
    g = r["results"][0]
    assert g["decided_by"] == "task", g
    assert g["frozen"] is True, g


def test_analyze_horizontal_spread(tmp_path):
    # changing REQ-010 must pull REQ-022 as verify via shared Customer.credit_limit
    mx = _matrix(tmp_path)
    r = run("analyze", "--matrix", str(mx), "--changed", "REQ-010")
    apply_refs = {i["ref"] for i in r["apply"]}
    assert "Customer.credit_limit" in apply_refs, apply_refs
    assert "customer.py:set_limit" in apply_refs, apply_refs
    verify_reqs = {v["req"] for v in r["verify"]}
    assert verify_reqs == {"REQ-022"}, verify_reqs
    assert any(v["shared_ref"] == "Customer.credit_limit" for v in r["verify"])


def test_analyze_unknown_req(tmp_path):
    mx = _matrix(tmp_path)
    r = run("analyze", "--matrix", str(mx), "--changed", "REQ-999")
    assert r["unknown_reqs"] == ["REQ-999"], r["unknown_reqs"]


def test_detect_declared_split(tmp_path):
    mx = _matrix(tmp_path)
    r = run("detect", "--matrix", str(mx), "--declared", "REQ-010,REQ-777",
            "--project-root", str(tmp_path))
    assert "REQ-010" in r["changed_set"], r
    assert r["declared_invalid"] == ["REQ-777"], r
    # B7-1: clean declared change (no untraced git files) → not blocked, cascade_required true
    assert r["status"] == "ok", r
    assert r["cascade_required"] is True, r


def test_detect_empty_changeset_noop(tmp_path):
    mx = _matrix(tmp_path)
    run("detect", "--matrix", str(mx), "--project-root", str(tmp_path), expect_code=2)


def test_detect_matrix_missing_blocked(tmp_path):
    r = run("detect", "--matrix", str(tmp_path / "nope.md"), "--declared", "REQ-010",
            "--project-root", str(tmp_path), expect_code=1)
    assert r["blocked"] == "matrix_not_found", r


def test_detect_untraced_change_blocks(tmp_path):
    # B7-1: a changed file in a git repo that maps to no REQ → status blocked,
    # reason untraced_change, exit 1 (cascade ENFORCED, not a silent note).
    mx = _matrix(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path)
    # an untracked file that is not referenced by any matrix code/test/design ref
    (tmp_path / "orphan_feature.py").write_text("x = 1\n", encoding="utf-8")
    r = run("detect", "--matrix", str(mx), "--project-root", str(tmp_path), expect_code=1)
    assert r["status"] == "blocked", r
    assert r["reason"] == "untraced_change", r
    assert "orphan_feature.py" in r["untraced_changes"], r


def test_freeze_matrix_priority_and_fallback(tmp_path):
    mx = _matrix(tmp_path)
    r = run("freeze", "--matrix", str(mx), "--reqs", "REQ-030,REQ-010",
            "--project-root", str(tmp_path))
    by = {x["req"]: x for x in r["results"]}
    assert by["REQ-030"]["frozen"] is True and by["REQ-030"]["decided_by"] == "matrix", by["REQ-030"]
    assert by["REQ-010"]["frozen"] is False and by["REQ-010"]["decided_by"] == "none", by["REQ-010"]


def test_freeze_phase_gate_tier(tmp_path):
    mx = _matrix(tmp_path)
    gates = tmp_path / "gates"; gates.mkdir(exist_ok=True)
    (gates / "phase-2-gate.md").write_text("status: PASSED\n", encoding="utf-8")
    r = run("freeze", "--matrix", str(mx), "--reqs", "REQ-010",
            "--gate-reports-glob", str(gates / "phase-*-gate.md"), "--project-root", str(tmp_path))
    g = r["results"][0]
    assert g["phase_gate"] == "PASSED", r
    assert g["frozen"] is True and g["decided_by"] == "phase-gate", g


def test_complete_set_difference(tmp_path):
    state = tmp_path / ".cascade-state.json"
    state.write_text(json.dumps({"cascade_in_progress": True,
                                 "dispositions": {"REQ-010": "reconciled"}}), encoding="utf-8")
    r = run("complete", "--state", str(state), "--changed", "REQ-010,REQ-022")
    assert r["missing"] == ["REQ-022"] and r["accounted"] == ["REQ-010"], r
    assert r["complete"] is False, r
    r = run("complete", "--state", str(tmp_path / "absent.json"), "--changed", "REQ-010")
    assert r["missing"] == ["REQ-010"], r


def test_complete_logs_cascade_round(tmp_path):
    # CLN-1: a COMPLETED cascade round appends exactly one line to
    # .cascade-log.jsonl beside the state file → re-cascade becomes measurable.
    state = tmp_path / ".cascade-state.json"
    state.write_text(json.dumps({"dispositions": {"REQ-010": "reconciled",
                                                   "REQ-022": "deferred"}}), encoding="utf-8")
    out = run("complete", "--state", str(state), "--changed", "REQ-010, REQ-022")
    assert out["complete"] is True and out["cascade_round"] == 1, out
    log = tmp_path / ".cascade-log.jsonl"
    assert log.exists()
    assert len([l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]) == 1
    # a second completed round increments the count
    out2 = run("complete", "--state", str(state), "--changed", "REQ-010, REQ-022")
    assert out2["cascade_round"] == 2, out2
    assert len([l for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]) == 2


def test_complete_incomplete_does_not_log(tmp_path):
    # An incomplete round (missing disposition) is NOT a cascade round → no log.
    state = tmp_path / ".cascade-state.json"
    state.write_text(json.dumps({"dispositions": {"REQ-010": "reconciled"}}), encoding="utf-8")
    out = run("complete", "--state", str(state), "--changed", "REQ-010, REQ-022")
    assert out["complete"] is False and out["cascade_round"] is None, out
    assert not (tmp_path / ".cascade-log.jsonl").exists()


if __name__ == "__main__":
    import tempfile
    for fn in [test_freeze_task_tier_done, test_analyze_horizontal_spread,
               test_analyze_unknown_req, test_detect_declared_split,
               test_detect_empty_changeset_noop, test_detect_matrix_missing_blocked,
               test_detect_untraced_change_blocks, test_freeze_matrix_priority_and_fallback,
               test_freeze_phase_gate_tier, test_complete_set_difference,
               test_complete_logs_cascade_round, test_complete_incomplete_does_not_log]:
        fn(Path(tempfile.mkdtemp()))
    print("ALL PASS")
