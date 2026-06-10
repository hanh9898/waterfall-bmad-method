#!/usr/bin/env python3
"""Tests for validate-implementation.py (D2)."""

import os
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "validate_implementation",
    os.path.join(os.path.dirname(__file__), "..", "validate-implementation.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

check_done_tasks = mod.check_done_tasks
check_matrix = mod.check_matrix
validate = mod.validate

TASKS = """\
# Task Breakdown

| task_id | description | design_ref | test_refs | priority | status | dependencies |
|---------|-------------|------------|-----------|----------|--------|--------------|
| TASK-001 | Login form | D-19 User | TC-001 | High | DONE | - |
| TASK-002 | Logout | D-19 Session | TC-002 | Med | TODO | TASK-001 |
"""

TASKS_DONE_NO_TEST = """\
# Task Breakdown

| task_id | description | design_ref | test_refs | priority | status | dependencies |
|---------|-------------|------------|-----------|----------|--------|--------------|
| TASK-001 | Login form | D-19 User | - | High | DONE | - |
"""


def _w(d, name, body):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    return p


def test_done_task_with_test_is_clean():
    assert check_done_tasks(TASKS) == []


def test_done_task_without_test_flagged():
    issues = check_done_tasks(TASKS_DONE_NO_TEST)
    assert [i for i in issues if i["type"] == "DONE_TASK_NO_TEST"]
    # a TODO task with no test is NOT flagged (only DONE work must be tested)
    assert all(i["task_id"] == "TASK-001" for i in issues)


def test_matrix_missing_code_file_flagged(tmp_path):
    matrix = (
        "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
        "|--------|----------|------------|----------|----------|-------------|-----------|\n"
        "| REQ-001 | - | D-19 | src/missing.py | TC-001 | - | - |\n"
    )
    issues = check_matrix(matrix, str(tmp_path))
    assert [i for i in issues if i["type"] == "MISSING_CODE_FILE"]


def test_matrix_existing_code_file_ok(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "login.py").write_text("x = 1\n", encoding="utf-8")
    matrix = (
        "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
        "|--------|----------|------------|----------|----------|-------------|-----------|\n"
        "| REQ-001 | - | D-19 | src/login.py | TC-001 | - | - |\n"
    )
    issues = check_matrix(matrix, str(tmp_path))
    assert not [i for i in issues if i["type"] == "MISSING_CODE_FILE"]


def test_matrix_designed_tested_not_implemented_flagged(tmp_path):
    matrix = (
        "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
        "|--------|----------|------------|----------|----------|-------------|-----------|\n"
        "| REQ-001 | - | D-19 User | - | TC-001 | - | - |\n"
    )
    issues = check_matrix(matrix, str(tmp_path))
    assert [i for i in issues if i["type"] == "REQ_NOT_IMPLEMENTED"]


def test_validate_clean_passes(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "login.py").write_text("x = 1\n", encoding="utf-8")
    tasks = _w(str(tmp_path), "task-breakdown.md", TASKS)
    matrix = _w(
        str(tmp_path), "matrix.md",
        "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
        "|--------|----------|------------|----------|----------|-------------|-----------|\n"
        "| REQ-001 | - | D-19 | src/login.py | TC-001 | PASSED | - |\n",
    )
    result = validate(tasks, matrix, str(tmp_path))
    assert result["valid"] is True
    assert result["structure_ok"] is True
    assert result["semantic_review"] == "n/a"


def test_validate_flags_and_exit(tmp_path):
    tasks = _w(str(tmp_path), "task-breakdown.md", TASKS_DONE_NO_TEST)
    result = validate(tasks)
    assert result["valid"] is False
    assert result["total_issues"] >= 1


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
