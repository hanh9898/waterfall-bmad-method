#!/usr/bin/env python3
"""Tests for validate-task-breakdown.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "validate_task_breakdown",
    os.path.join(os.path.dirname(__file__), "..", "validate-task-breakdown.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

validate = mod.validate
check_task_ids = mod.check_task_ids
check_dependencies = mod.check_dependencies
check_entity_coverage = mod.check_entity_coverage
check_test_assignment = mod.check_test_assignment


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


MINIMAL_VALID = """---
title: "Test Project Task Breakdown"
total_tasks: 3
completed: 0
coverage_pct: 0
updated: "2026-05-28"
---

## Task List

| task_id | description | design_ref | test_refs | priority | status | dependencies |
|---------|-------------|------------|-----------|----------|--------|--------------|
| TASK-001 | Create User model and migration | User entity | TC-001, TC-002 | 1 | TODO | - |
| TASK-002 | Create Order model with FK to User | Order entity | TC-003 | 2 | TODO | TASK-001 |
| TASK-003 | Implement Order API endpoints | Order API | TC-004, TC-005 | 3 | TODO | TASK-001, TASK-002 |
"""

D19_WITH_ENTITIES = """# Database Design

```mermaid
erDiagram
    User {
        int id PK
        string name
        string email
    }
    Order {
        int id PK
        int user_id FK
        float total
    }
    User ||--o{ Order : places
```
"""

D27_WITH_TCS = """# Test Specification

## Test Cases

### TC-001: User creation
**REQ ID:** REQ-001
**Severity:** High

### TC-002: User validation
**REQ ID:** REQ-001
**Severity:** Medium

### TC-003: Order creation
**REQ ID:** REQ-002
**Severity:** High

### TC-004: Order API list
**REQ ID:** REQ-003
**Severity:** Medium

### TC-005: Order API create
**REQ ID:** REQ-003
**Severity:** High
"""


class TestCheckTaskIds:
    def test_valid_ids(self):
        issues = check_task_ids(MINIMAL_VALID)
        assert len(issues) == 0

    def test_no_tasks(self):
        content = "# Empty\n\nNo tasks here."
        issues = check_task_ids(content)
        assert len(issues) == 1
        assert issues[0]["type"] == "NO_TASKS"

    def test_duplicate_ids(self):
        content = MINIMAL_VALID + (
            "| TASK-001 | Duplicate task | Dup | TC-006 | 4 | TODO | - |\n"
        )
        issues = check_task_ids(content)
        dups = [i for i in issues if i["type"] == "TASK_ID_DUPLICATE"]
        assert len(dups) == 1
        assert "TASK-001" in dups[0]["message"]


class TestCheckDependencies:
    def test_valid_dependencies(self):
        issues = check_dependencies(MINIMAL_VALID)
        assert len(issues) == 0

    def test_unknown_dependency(self):
        content = MINIMAL_VALID.replace(
            "| TASK-003 | Implement Order API endpoints | Order API | TC-004, TC-005 | 3 | TODO | TASK-001, TASK-002 |",
            "| TASK-003 | Implement Order API endpoints | Order API | TC-004, TC-005 | 3 | TODO | TASK-001, TASK-999 |",
        )
        issues = check_dependencies(content)
        unknown = [i for i in issues if i["type"] == "UNKNOWN_DEPENDENCY"]
        assert len(unknown) == 1
        assert "TASK-999" in unknown[0]["message"]

    def test_dependency_order_violation(self):
        content = """
| task_id | description | design_ref | test_refs | priority | status | dependencies |
|---------|-------------|------------|-----------|----------|--------|--------------|
| TASK-001 | First | A | TC-001 | 1 | TODO | TASK-002 |
| TASK-002 | Second | B | TC-002 | 2 | TODO | - |
"""
        issues = check_dependencies(content)
        order = [i for i in issues if i["type"] == "DEPENDENCY_ORDER"]
        assert len(order) == 1
        assert "TASK-001" in order[0]["message"]

    def test_no_dependency_marker(self):
        content = """
| task_id | description | design_ref | test_refs | priority | status | dependencies |
|---------|-------------|------------|-----------|----------|--------|--------------|
| TASK-001 | First | A | TC-001 | 1 | TODO | - |
"""
        issues = check_dependencies(content)
        assert len(issues) == 0


class TestEntityCoverage:
    def test_all_entities_covered(self, tmp_path):
        d19_path = str(tmp_path / "d19.md")
        _write(d19_path, D19_WITH_ENTITIES)
        issues = check_entity_coverage(MINIMAL_VALID, d19_path)
        assert len(issues) == 0

    def test_missing_entity(self, tmp_path):
        d19_path = str(tmp_path / "d19.md")
        d19_with_extra = D19_WITH_ENTITIES.replace(
            "    User ||--o{ Order : places",
            "    Product {\n        int id PK\n        string name\n    }\n    User ||--o{ Order : places",
        )
        _write(d19_path, d19_with_extra)
        issues = check_entity_coverage(MINIMAL_VALID, d19_path)
        uncovered = [i for i in issues if i["type"] == "ENTITY_NOT_COVERED"]
        assert len(uncovered) == 1
        assert uncovered[0]["entity"] == "Product"

    def test_entity_in_prose_not_counted(self, tmp_path):
        # S-4: an entity named only in a task DESCRIPTION (not design_ref) is NOT covered
        d19_path = str(tmp_path / "d19.md")
        d19 = D19_WITH_ENTITIES.replace(
            "    User ||--o{ Order : places",
            "    Payment {\n        int id PK\n    }\n    User ||--o{ Order : places",
        )
        _write(d19_path, d19)
        tb = MINIMAL_VALID.replace(
            "Implement Order API endpoints",
            "Implement Order API endpoints incl Payment hook",
        )
        issues = check_entity_coverage(tb, d19_path)
        uncovered = [i for i in issues if i["type"] == "ENTITY_NOT_COVERED"]
        assert any(i["entity"] == "Payment" for i in uncovered), uncovered

    def test_no_d19_path(self):
        issues = check_entity_coverage(MINIMAL_VALID, None)
        assert len(issues) == 0

    def test_d19_no_er_diagram(self, tmp_path):
        d19_path = str(tmp_path / "d19.md")
        _write(d19_path, "# DB Design\n\nNo ER diagram here.")
        issues = check_entity_coverage(MINIMAL_VALID, d19_path)
        assert len(issues) == 0

    def test_d19_file_not_found(self):
        issues = check_entity_coverage(MINIMAL_VALID, "/nonexistent/d19.md")
        assert len(issues) == 0


class TestTestAssignment:
    def test_all_tcs_assigned(self, tmp_path):
        d27_path = str(tmp_path / "d27.md")
        _write(d27_path, D27_WITH_TCS)
        issues = check_test_assignment(MINIMAL_VALID, d27_path)
        assert len(issues) == 0

    def test_unassigned_tc(self, tmp_path):
        d27_path = str(tmp_path / "d27.md")
        d27_extra = D27_WITH_TCS + "\n### TC-006: Unassigned test\n**REQ ID:** REQ-004\n"
        _write(d27_path, d27_extra)
        issues = check_test_assignment(MINIMAL_VALID, d27_path)
        unassigned = [i for i in issues if i["type"] == "TC_UNASSIGNED"]
        assert len(unassigned) == 1
        assert unassigned[0]["tc_id"] == "TC-006"

    def test_no_d27_path(self):
        issues = check_test_assignment(MINIMAL_VALID, None)
        assert len(issues) == 0


class TestFullValidation:
    def test_valid_document(self, tmp_path):
        path = str(tmp_path / "tb.md")
        _write(path, MINIMAL_VALID)
        result = validate(path)
        assert result["valid"] is True
        assert result["total_tasks"] == 3
        assert result["total_issues"] == 0
        # honest verdict (S-3)
        assert result["structure_ok"] is True
        assert result["semantic_review"] == "n/a"
        assert result["passed"] is True

    def test_invalid_document(self, tmp_path):
        path = str(tmp_path / "tb.md")
        _write(path, "# Empty\n\nNo tasks.")
        result = validate(path)
        assert result["valid"] is False
        assert result["total_tasks"] == 0

    def test_with_d19_and_d27(self, tmp_path):
        tb_path = str(tmp_path / "tb.md")
        d19_path = str(tmp_path / "d19.md")
        d27_path = str(tmp_path / "d27.md")
        _write(tb_path, MINIMAL_VALID)
        _write(d19_path, D19_WITH_ENTITIES)
        _write(d27_path, D27_WITH_TCS)
        result = validate(tb_path, d19_path, d27_path)
        assert result["valid"] is True

    def test_cli_exit_code(self, tmp_path):
        import subprocess

        path = str(tmp_path / "tb.md")
        _write(path, MINIMAL_VALID)
        script = os.path.join(os.path.dirname(__file__), "..", "validate-task-breakdown.py")
        result = subprocess.run([sys.executable, script, path], capture_output=True)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True

    def test_cli_invalid_exit_code(self, tmp_path):
        import subprocess

        path = str(tmp_path / "tb.md")
        _write(path, "# Empty\n\nNo tasks.")
        script = os.path.join(os.path.dirname(__file__), "..", "validate-task-breakdown.py")
        result = subprocess.run([sys.executable, script, path], capture_output=True)
        assert result.returncode == 1
