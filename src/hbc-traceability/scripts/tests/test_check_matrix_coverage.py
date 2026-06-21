#!/usr/bin/env python3
"""Tests for check-matrix-coverage.py (T1.5)."""

import os
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "check_matrix_coverage",
    os.path.join(os.path.dirname(__file__), "..", "check-matrix-coverage.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)
check = mod.check

D02 = """
REQ-FEAT-001, REQ-FEAT-002, REQ-FEAT-003 and the late REQ-FEAT-040.
"""
MATRIX = """
| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | ts |
|---|---|---|---|---|---|---|---|
| feat | REQ-FEAT-001 |  | D-19 | a.py | TC-001 |  | d |
| feat | REQ-FEAT-002 |  | D-19 | b.py | TC-002 |  | d |
| feat | REQ-FEAT-003 |  |  |  |  |  | d |
"""


def test_missing_and_untraced_flagged():
    r = check(D02, MATRIX)
    types = {i["type"] for i in r["issues"]}
    assert r["valid"] is False
    assert "MISSING_FROM_MATRIX" in types  # REQ-040 has no row
    assert "UNTRACED_COLUMN" in types       # REQ-003 row traces nothing
    missing = [i["req_id"] for i in r["issues"] if i["type"] == "MISSING_FROM_MATRIX"]
    assert missing == ["REQ-FEAT-040"]


def test_req_without_task_only_with_tasks():
    tasks = "| TASK-001 | REQ-FEAT-001 |\n| TASK-002 | REQ-FEAT-002 |"
    r = check(D02, MATRIX, tasks)
    untasked = sorted(i["req_id"] for i in r["issues"] if i["type"] == "REQ_WITHOUT_TASK")
    assert "REQ-FEAT-003" in untasked and "REQ-FEAT-040" in untasked


def test_clean_matrix_passes():
    d02 = "REQ-FEAT-001"
    matrix = (
        "| req_id | design_ref | code_ref | test_ref |\n"
        "|---|---|---|---|\n"
        "| REQ-FEAT-001 | D-19 | a.py | TC-001 |\n"
    )
    r = check(d02, matrix)
    assert r["valid"] is True and r["total_issues"] == 0


def test_multi_feature_warning():
    d02 = "REQ-ALPHA-001 and REQ-BETA-001"
    matrix = "| req_id | design_ref | code_ref | test_ref |\n|---|---|---|---|\n| REQ-ALPHA-001 | D | a | T |\n"
    r = check(d02, matrix)
    assert "multi_feature_warning" in r


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
