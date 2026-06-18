#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for impact.py (detect / analyze / freeze). Run: python test-impact.py"""

import json
import subprocess
import sys
import tempfile
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


def test_freeze_task_tier_done(tmp_path):
    # Bug H1: a DONE task whose refs match a REQ's matrix refs must freeze it via
    # the task tier. The old space-join + ',;'-only split collapsed the three ref
    # columns into one token that never matched a task blob, so the tier never fired.
    mx = tmp_path / "matrix.md"
    mx.write_text(MATRIX, encoding="utf-8")
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


def main():
    tmp = Path(tempfile.mkdtemp())
    mx = tmp / "matrix.md"
    mx.write_text(MATRIX, encoding="utf-8")

    # analyze: changing REQ-010 must pull REQ-022 as verify via shared Customer.credit_limit
    r = run("analyze", "--matrix", str(mx), "--changed", "REQ-010")
    apply_refs = {i["ref"] for i in r["apply"]}
    assert "Customer.credit_limit" in apply_refs, apply_refs
    assert "customer.py:set_limit" in apply_refs, apply_refs
    verify_reqs = {v["req"] for v in r["verify"]}
    assert verify_reqs == {"REQ-022"}, verify_reqs
    assert any(v["shared_ref"] == "Customer.credit_limit" for v in r["verify"])
    print("ok analyze: lan-ngang REQ-022 detected")

    # analyze: unknown changed req surfaces, no crash
    r = run("analyze", "--matrix", str(mx), "--changed", "REQ-999")
    assert r["unknown_reqs"] == ["REQ-999"], r["unknown_reqs"]
    print("ok analyze: unknown req surfaced")

    # detect: declared valid -> changed_set; invalid surfaced
    r = run("detect", "--matrix", str(mx), "--declared", "REQ-010,REQ-777",
            "--project-root", str(tmp))
    assert "REQ-010" in r["changed_set"], r
    assert r["declared_invalid"] == ["REQ-777"], r
    print("ok detect: declared valid/invalid split")

    # detect: nothing declared + not a git repo -> no-op exit 2
    run("detect", "--matrix", str(mx), "--project-root", str(tmp), expect_code=2)
    print("ok detect: empty changeset -> no-op exit 2")

    # detect: matrix missing -> blocked exit 1
    r = run("detect", "--matrix", str(tmp / "nope.md"), "--declared", "REQ-010",
            "--project-root", str(tmp), expect_code=1)
    assert r["blocked"] == "matrix_not_found", r
    print("ok detect: matrix missing -> blocked")

    # freeze: REQ-030 matrix gate PASSED, no task/gate -> frozen via matrix
    r = run("freeze", "--matrix", str(mx), "--reqs", "REQ-030,REQ-010",
            "--project-root", str(tmp))
    by = {x["req"]: x for x in r["results"]}
    assert by["REQ-030"]["frozen"] is True and by["REQ-030"]["decided_by"] == "matrix", by["REQ-030"]
    assert by["REQ-010"]["frozen"] is False and by["REQ-010"]["decided_by"] == "none", by["REQ-010"]
    print("ok freeze: matrix-gate priority + fallback")

    # freeze: phase-gate tier via glob (locks the _gate_status path fix)
    gates = tmp / "gates"; gates.mkdir(exist_ok=True)
    (gates / "phase-2-gate.md").write_text("status: PASSED\n", encoding="utf-8")
    r = run("freeze", "--matrix", str(mx), "--reqs", "REQ-010",
            "--gate-reports-glob", str(gates / "phase-*-gate.md"), "--project-root", str(tmp))
    g = r["results"][0]
    assert g["phase_gate"] == "PASSED", r
    assert g["frozen"] is True and g["decided_by"] == "phase-gate", g
    print("ok freeze: phase-gate tier via glob")

    # complete: changed-set minus accounted dispositions
    state = tmp / ".cascade-state.json"
    state.write_text(json.dumps({"cascade_in_progress": True,
                                 "dispositions": {"REQ-010": "reconciled"}}), encoding="utf-8")
    r = run("complete", "--state", str(state), "--changed", "REQ-010,REQ-022")
    assert r["missing"] == ["REQ-022"] and r["accounted"] == ["REQ-010"], r
    assert r["complete"] is False, r
    # no state file -> everything missing
    r = run("complete", "--state", str(tmp / "absent.json"), "--changed", "REQ-010")
    assert r["missing"] == ["REQ-010"], r
    print("ok complete: set-difference of dispositions")

    print("\nALL PASS")


if __name__ == "__main__":
    main()
