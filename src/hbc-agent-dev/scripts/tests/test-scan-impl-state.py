#!/usr/bin/env python3
"""Tests for scan-impl-state.py."""

import json
import os
import subprocess
import sys

import pytest
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "scan_impl_state",
    os.path.join(os.path.dirname(__file__), "..", "scan-impl-state.py"),
)
assert _spec is not None and _spec.loader is not None
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

scan = mod.scan
read_frontmatter_date = mod.read_frontmatter_date
count_tasks = mod.count_tasks


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


TASK_BREAKDOWN_MIXED = """\
---
updated: 2026-05-25
---
# Task Breakdown

- [x] TASK-001 Set up project structure
- [x] TASK-002 Create database schema
- [x] TASK-003 Implement user model
- [ ] TASK-004 Implement auth endpoints IN_PROGRESS
- [ ] TASK-005 Add validation middleware
- [ ] TASK-006 Write integration tests
"""

TASK_BREAKDOWN_ALL_DONE = """\
---
updated: 2026-05-28
---
# Task Breakdown

- [x] TASK-001 Set up project structure
- [x] TASK-002 Create database schema
- [x] TASK-003 Implement user model
"""

TASK_BREAKDOWN_EMPTY = """\
---
updated: 2026-05-20
---
# Task Breakdown

No tasks defined yet.
"""


class TestNoTaskBreakdown:
    def test_empty_dir_returns_blocked(self, tmp_path):
        result = scan(str(tmp_path))
        assert result["status"] == "blocked"
        assert result["next_recommended"] == "TB"
        assert "task breakdown" in result["reason"].lower()
        state = result["impl_state"]
        assert state["task_breakdown"]["exists"] is False
        assert state["total_tasks"] == 0
        assert state["done"] == 0
        assert state["in_progress"] == 0
        assert state["todo"] == 0
        assert state["coverage"] is None

    def test_nonexistent_dir_via_scan(self, tmp_path):
        result = scan(str(tmp_path / "nonexistent"))
        assert result["status"] == "blocked"
        assert result["impl_state"]["task_breakdown"]["exists"] is False


class TestEmptyTaskBreakdown:
    def test_file_exists_but_no_tasks(self, tmp_path):
        _write(str(tmp_path / "task-breakdown.md"), TASK_BREAKDOWN_EMPTY)
        result = scan(str(tmp_path))
        assert result["status"] == "blocked"
        assert result["next_recommended"] == "TB"
        state = result["impl_state"]
        assert state["task_breakdown"]["exists"] is True
        assert state["total_tasks"] == 0
        assert state["done"] == 0


class TestMixedStatuses:
    def test_mixed_tasks_returns_blocked(self, tmp_path):
        _write(str(tmp_path / "task-breakdown.md"), TASK_BREAKDOWN_MIXED)
        result = scan(str(tmp_path))
        assert result["status"] == "blocked"
        assert result["next_recommended"] == "IM"
        state = result["impl_state"]
        assert state["task_breakdown"]["exists"] is True
        assert state["task_breakdown"]["file"] == "task-breakdown.md"
        assert state["task_breakdown"]["updated"] == "2026-05-25"
        assert state["done"] == 3
        assert state["in_progress"] == 1
        assert state["todo"] == 2
        assert state["total_tasks"] == 6
        assert "3 tasks remaining" in result["reason"]

    def test_next_task_id_in_reason(self, tmp_path):
        _write(str(tmp_path / "task-breakdown.md"), TASK_BREAKDOWN_MIXED)
        result = scan(str(tmp_path))
        assert "TASK-004" in result["reason"]

    def test_in_progress_marker_emoji(self, tmp_path):
        content = "- [x] TASK-001 Done\n- [ ] TASK-002 Working 🔄\n- [ ] TASK-003 Pending\n"
        _write(str(tmp_path / "task-breakdown.md"), content)
        result = scan(str(tmp_path))
        assert result["impl_state"]["in_progress"] == 1
        assert result["impl_state"]["todo"] == 1
        assert result["impl_state"]["done"] == 1


class TestAllDone:
    def test_all_tasks_done_returns_complete(self, tmp_path):
        _write(str(tmp_path / "task-breakdown.md"), TASK_BREAKDOWN_ALL_DONE)
        result = scan(str(tmp_path))
        assert result["status"] == "complete"
        assert result["next_recommended"] == "PG"
        assert "gate" in result["reason"].lower()
        state = result["impl_state"]
        assert state["done"] == 3
        assert state["in_progress"] == 0
        assert state["todo"] == 0
        assert state["total_tasks"] == 3


class TestCoverageDetection:
    def test_detects_coverage_json(self, tmp_path):
        coverage_data = {"totals": {"percent_covered": 85.5}}
        _write(str(tmp_path / "coverage.json"), json.dumps(coverage_data))
        _write(str(tmp_path / "task-breakdown.md"), TASK_BREAKDOWN_MIXED)
        result = scan(str(tmp_path))
        assert result["impl_state"]["coverage"] == 85.5

    def test_no_coverage_returns_none(self, tmp_path):
        isolated = tmp_path / "isolated" / "impl"
        isolated.mkdir(parents=True)
        _write(str(isolated / "task-breakdown.md"), TASK_BREAKDOWN_MIXED)
        result = scan(str(isolated))
        assert result["impl_state"]["coverage"] is None

    def test_malformed_coverage_returns_none(self, tmp_path):
        _write(str(tmp_path / "coverage.json"), "{invalid json")
        _write(str(tmp_path / "task-breakdown.md"), TASK_BREAKDOWN_MIXED)
        result = scan(str(tmp_path))
        assert result["impl_state"]["coverage"] is None


class TestFrontmatterDate:
    def test_extracts_updated_date(self, tmp_path):
        content = "---\nupdated: 2026-05-25\ntitle: Test\n---\n# Content"
        path = str(tmp_path / "task-breakdown.md")
        _write(path, content)
        assert read_frontmatter_date(path) == "2026-05-25"

    def test_extracts_last_touched(self, tmp_path):
        content = "---\nlast_touched: 2026-05-20\n---\n# Content"
        path = str(tmp_path / "task-breakdown.md")
        _write(path, content)
        assert read_frontmatter_date(path) == "2026-05-20"

    def test_no_frontmatter_returns_none(self, tmp_path):
        path = str(tmp_path / "task-breakdown.md")
        _write(path, "# No frontmatter")
        assert read_frontmatter_date(path) is None


class TestCountTasks:
    def test_empty_content(self):
        result = count_tasks("")
        assert result == {"done": 0, "in_progress": 0, "todo": 0}

    def test_mixed_content(self):
        result = count_tasks(TASK_BREAKDOWN_MIXED)
        assert result["done"] == 3
        assert result["in_progress"] == 1
        assert result["todo"] == 2

    def test_case_insensitive_done(self):
        content = "- [X] TASK-001 Done\n- [x] TASK-002 Also done\n"
        result = count_tasks(content)
        assert result["done"] == 2


class TestPhase3Gate:
    def test_no_gate_reports_absent(self, tmp_path):
        _write(str(tmp_path / "task-breakdown.md"), TASK_BREAKDOWN_MIXED)
        result = scan(str(tmp_path))
        gate = result["impl_state"]["phase-3-gate"]
        assert gate == {"exists": False, "file": None, "path": None, "updated": None}

    def test_gate_in_gates_dir_detected(self, tmp_path):
        _write(str(tmp_path / "task-breakdown.md"), TASK_BREAKDOWN_MIXED)
        gates = tmp_path / "gates"
        _write(str(gates / "phase-3-gate.md"), "---\nupdated: 2026-06-02\n---\n**Status:** PASSED\n")
        result = scan(str(tmp_path), gates_dir=str(gates))
        gate = result["impl_state"]["phase-3-gate"]
        assert gate["exists"] is True
        assert gate["file"] == "phase-3-gate.md"
        assert gate["updated"] == "2026-06-02"

    def test_gate_falls_back_to_output_path(self, tmp_path):
        _write(str(tmp_path / "task-breakdown.md"), TASK_BREAKDOWN_MIXED)
        _write(str(tmp_path / "phase-3-gate-results.json"), "{}")
        result = scan(str(tmp_path))  # no gates_dir → search output_path
        assert result["impl_state"]["phase-3-gate"]["exists"] is True


class TestOutputToFile:
    def test_writes_json_to_file(self, tmp_path):
        scan_dir = tmp_path / "artifacts"
        scan_dir.mkdir()
        out_file = str(tmp_path / "result.json")
        _write(str(scan_dir / "task-breakdown.md"), TASK_BREAKDOWN_MIXED)

        script = os.path.join(
            os.path.dirname(__file__), "..", "scan-impl-state.py"
        )
        result = subprocess.run(
            [sys.executable, script, str(scan_dir), "-o", out_file],
            capture_output=True,
        )
        assert result.returncode == 0
        with open(out_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["status"] == "blocked"
        assert data["impl_state"]["task_breakdown"]["exists"] is True
        assert data["impl_state"]["done"] == 3
