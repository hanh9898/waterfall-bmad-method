#!/usr/bin/env python3
"""Tests for check-task-coverage.py (B4-7 every REQ->task / B4-2 input-set declared)."""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-task-coverage.py")
REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE = REPO_ROOT / "process-review" / "fixtures" / "resource-plan-billable" / "artifacts"

# A breakdown declaring all four input dimensions and covering REQ-001..003,
# including the slash-shorthand the RCA breakdown uses.
TB_GOOD = """\
---
title: "Demo Task Breakdown"
total_tasks: 2
sources:
  - D-02 v2.0 (requirements / yêu cầu REQ-)
  - D-06 v1.1 (business flow paths, PATH-)
  - acceptance criteria per REQ (AC-)
  - code-reality classified NEW / CHANGE / already-exists
---

## Task List

| task_id | description | req_refs | design_ref | test_refs | code_reality | priority | status | dependencies |
|---------|-------------|----------|------------|-----------|--------------|----------|--------|--------------|
| TASK-001 | Slice plan CRUD (REQ-001/002) | REQ-001/002 | Plan | TC-001 | NEW | 1 | TODO | - |
| TASK-002 | Slice approval rule REQ-003 | REQ-003 | Plan.state | TC-002 | CHANGE | 2 | TODO | TASK-001 |
"""

D02 = """\
---
document_id: D-02
version: "2.0"
---

# Requirements

| id | title |
|----|-------|
| REQ-DEMO-001 | Create plan |
| REQ-DEMO-002 | Edit plan |
| REQ-DEMO-003 | Approve plan |
"""


def write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


def run(args: list[str]) -> tuple[dict, int]:
    r = subprocess.run(
        [sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding="utf-8"
    )
    return json.loads(r.stdout), r.returncode


class TestReqCoverage:
    def test_all_reqs_covered_via_slash_shorthand(self, tmp_path):
        tb = write(tmp_path, "tb.md", TB_GOOD)
        d02 = write(tmp_path, "d02.md", D02)
        data, code = run([str(tb), "--d02", str(d02)])
        # REQ-002 is only present via the `REQ-001/002` shorthand — must NOT be flagged
        assert data["reqs_without_task"] == [], data["reqs_without_task"]
        assert code == 0
        assert data["grounded"] is True

    def test_missing_req_flagged(self, tmp_path):
        d02_extra = D02 + "| REQ-DEMO-004 | Reject plan |\n"
        tb = write(tmp_path, "tb.md", TB_GOOD)
        d02 = write(tmp_path, "d02.md", d02_extra)
        data, code = run([str(tb), "--d02", str(d02)])
        nums = [r for r in data["reqs_without_task"] if r.endswith("004")]
        assert len(nums) == 1, data["reqs_without_task"]
        assert code == 1
        assert any(i["type"] == "REQ_WITHOUT_TASK" for i in data["issues"])

    def test_canonical_and_bare_reconcile(self, tmp_path):
        # breakdown cites bare REQ-001; D-02 defines canonical REQ-DEMO-001 — same slice
        tb = write(tmp_path, "tb.md", TB_GOOD)
        d02 = write(tmp_path, "d02.md", D02)
        data, _ = run([str(tb), "--d02", str(d02)])
        assert "REQ-DEMO-001" not in data["reqs_without_task"]

    def test_no_d02_skips_coverage(self, tmp_path):
        tb = write(tmp_path, "tb.md", TB_GOOD)
        data, code = run([str(tb)])
        assert data["grounded"] is False
        assert data["reqs_without_task"] == []
        # input set is fully declared, so still valid
        assert code == 0


class TestInputGaps:
    def test_all_dimensions_declared(self, tmp_path):
        tb = write(tmp_path, "tb.md", TB_GOOD)
        data, _ = run([str(tb)])
        assert data["input_gaps"] == [], data["input_gaps"]

    def test_missing_dimensions_flagged(self, tmp_path):
        thin = """\
---
title: "Thin"
---

## Task List

| task_id | description | priority | status | dependencies |
|---------|-------------|----------|--------|--------------|
| TASK-001 | do a thing | 1 | TODO | - |
"""
        tb = write(tmp_path, "tb.md", thin)
        data, code = run([str(tb)])
        # no REQ-/D-06/AC/code-reality markers at all
        for dim in ("requirements_d02", "business_flow_d06", "acceptance_criteria", "code_reality"):
            assert dim in data["input_gaps"], data["input_gaps"]
        assert code == 1
        assert any(i["type"] == "INPUT_INSUFFICIENT" for i in data["issues"])


class TestChurnAndVerdict:
    def test_churn_block_present(self, tmp_path):
        tb = write(tmp_path, "tb.md", TB_GOOD)
        data, _ = run([str(tb)])
        assert "churn" in data
        assert data["churn"]["high_churn"] is False
        # honest verdict
        assert data["semantic_review"] == "n/a"
        assert data["structure_ok"] is True


class TestErrorHandling:
    def test_missing_document_is_loud(self, tmp_path):
        data, code = run([str(tmp_path / "nope.md")])
        assert code == 2
        assert "error" in data

    def test_missing_d02_is_loud_not_silent(self, tmp_path):
        # a supplied-but-missing --d02 must be a loud arg error, never a silent
        # false-green (the glossary/coding-standards masking-bug class)
        tb = write(tmp_path, "tb.md", TB_GOOD)
        data, code = run([str(tb), "--d02", str(tmp_path / "missing.md")])
        assert code == 2
        assert "error" in data

    def test_project_root_resolves_relative(self, tmp_path):
        write(tmp_path, "tb.md", TB_GOOD)
        write(tmp_path, "d02.md", D02)
        data, code = run(["tb.md", "--project-root", str(tmp_path), "--d02", "d02.md"])
        assert code == 0
        assert data["reqs_without_task"] == []


class TestTwoWayCoverage:
    """TA.5 — the machine bidirectional 100%-rule (REQ<->task) as a view over the
    build-graph. Exercises both directions + the orphan/dangling distinction."""

    def test_clean_two_way_complete(self, tmp_path):
        # every D-02 REQ has a task AND every task cites a live REQ
        tb = write(tmp_path, "tb.md", TB_GOOD)
        d02 = write(tmp_path, "d02.md", D02)
        data, _ = run([str(tb), "--d02", str(d02)])
        cov = data["two_way_coverage"]
        assert cov["two_way_complete"] is True, cov
        assert cov["reqs_without_task"] == []
        assert cov["orphan_tasks"] == []

    def test_dangling_task_is_orphan(self, tmp_path):
        # a task citing REQ-999, which is NOT in D-02 (renumbered/removed) → orphan
        tb_text = TB_GOOD + (
            "| TASK-009 | stale slice REQ-999 | REQ-999 | Old | TC-099 | CHANGE | 9 | TODO | - |\n"
        )
        tb = write(tmp_path, "tb.md", tb_text)
        d02 = write(tmp_path, "d02.md", D02)
        data, code = run([str(tb), "--d02", str(d02)])
        cov = data["two_way_coverage"]
        orphans = {o["task_id"] for o in cov["orphan_tasks"]}
        assert "TASK-009" in orphans, cov["orphan_tasks"]
        assert cov["two_way_complete"] is False
        assert code == 1
        assert any(i["type"] == "ORPHAN_TASK" for i in data["issues"])

    def test_bare_cite_not_false_orphan(self, tmp_path):
        # TASK rows cite bare REQ-001/002/003; D-02 defines canonical REQ-DEMO-00x.
        # Trailing-number identity must reconcile — NO orphan from bare-vs-canonical.
        tb = write(tmp_path, "tb.md", TB_GOOD)
        d02 = write(tmp_path, "d02.md", D02)
        data, _ = run([str(tb), "--d02", str(d02)])
        assert data["two_way_coverage"]["orphan_tasks"] == []

    def test_task_without_req_is_advisory_not_orphan(self, tmp_path):
        # an infra/scaffold task citing zero REQ is reported separately and does NOT
        # fail the two-way rule on its own
        tb_text = TB_GOOD + (
            "| TASK-009 | infra scaffold manifest | | module | TC-099 | NEW | 9 | TODO | - |\n"
        )
        tb = write(tmp_path, "tb.md", tb_text)
        d02 = write(tmp_path, "d02.md", D02)
        data, _ = run([str(tb), "--d02", str(d02)])
        cov = data["two_way_coverage"]
        assert "TASK-009" in cov["tasks_without_req"], cov
        assert all(o["task_id"] != "TASK-009" for o in cov["orphan_tasks"])
        # no missing REQ and no orphan → still two-way complete despite the infra task
        assert cov["two_way_complete"] is True

    def test_no_d02_yields_null_coverage(self, tmp_path):
        tb = write(tmp_path, "tb.md", TB_GOOD)
        data, _ = run([str(tb)])
        assert data["two_way_coverage"] is None


class TestRealFixture:
    """TD.0 regression: the STALE breakdown (v1.8, 39 REQ) must surface the
    headline missing slices REQ-040/041/042 against the v2.3 D-02."""

    def _paths(self):
        tb = FIXTURE / "implementation-artifacts" / "task-breakdown.md"
        d02 = FIXTURE / "planning-artifacts" / "D-02-resource-plan-billable.md"
        return tb, d02

    def test_surfaces_040_041_042(self):
        tb, d02 = self._paths()
        if not tb.is_file() or not d02.is_file():
            import pytest

            pytest.skip("TD.0 fixture not present")
        data, code = run([str(tb), "--d02", str(d02)])
        missing_tail = {r[-3:] for r in data["reqs_without_task"]}
        assert {"040", "041", "042"} <= missing_tail, data["reqs_without_task"]
        assert code == 1

    def test_two_way_incomplete_on_broken_fixture(self):
        tb, d02 = self._paths()
        if not tb.is_file() or not d02.is_file():
            import pytest

            pytest.skip("TD.0 fixture not present")
        data, _ = run([str(tb), "--d02", str(d02)])
        cov = data["two_way_coverage"]
        assert cov["two_way_complete"] is False
        missing_tail = {r[-3:] for r in cov["reqs_without_task"]}
        assert {"040", "041", "042"} <= missing_tail, cov["reqs_without_task"]
