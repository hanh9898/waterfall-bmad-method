#!/usr/bin/env python3
"""Tests for trace-report.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "trace-report.py")


def run(matrix_path: str, extra_args: list[str] | None = None) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, "--matrix", matrix_path] + (extra_args or [])
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout.strip() else {"error": result.stderr}
    return data, result.returncode


def test_full_matrix():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Traceability Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | US-01 | Entity_User | auth.py:login | TC-001 | PASSED | 2026-05-26 |\n"
            "| REQ-002 | US-02 | Entity_Order | order.py:create | TC-002 | PASSED | 2026-05-26 |\n"
        )
        data, code = run(str(matrix))
        assert data["total_requirements"] == 2
        assert data["fully_traced"] == 2
        assert data["fully_traced_pct"] == 100.0
        assert data["gaps"] == []
        assert code == 0


def test_matrix_with_gaps():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | Entity_User | auth.py | TC-001 | | |\n"
            "| REQ-002 | | | | | | |\n"
            "| REQ-003 | | Entity_Log | | TC-003 | | |\n"
        )
        data, code = run(str(matrix))
        assert data["total_requirements"] == 3
        assert data["coverage"]["design_ref"] == 2
        assert data["coverage"]["code_ref"] == 1
        assert data["coverage"]["test_ref"] == 2
        assert data["fully_traced"] == 1
        assert "REQ-002" in data["gaps"]
        assert "REQ-003" in data["gaps"]
        assert code == 0  # gaps are data, not errors


def test_strict_mode_exits_1_on_gaps():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | | | | | |\n"
        )
        _, code = run(str(matrix), ["--strict"])
        assert code == 1


def test_empty_matrix():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
        )
        data, code = run(str(matrix))
        assert data["total_requirements"] == 0
        assert data["fully_traced"] == 0
        assert code == 0


def test_missing_matrix_file():
    data, code = run("/nonexistent/matrix.md")
    assert "error" in data or "suggestion" in data
    assert code == 1


def test_output_to_file():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | D-19 | src/a.py | TC-001 | | |\n"
        )
        out = Path(tmp) / "report.json"
        run(str(matrix), ["-o", str(out)])
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["total_requirements"] == 1


def test_gap_details_structure():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | | | TC-001 | | |\n"
        )
        data, _ = run(str(matrix))
        assert len(data["gap_details"]) == 1
        gap = data["gap_details"][0]
        assert gap["req_id"] == "REQ-001"
        assert "design_ref" in gap["missing_columns"]
        assert "code_ref" in gap["missing_columns"]
        assert "test_ref" not in gap["missing_columns"]


if __name__ == "__main__":
    test_full_matrix()
    test_matrix_with_gaps()
    test_strict_mode_exits_1_on_gaps()
    test_empty_matrix()
    test_missing_matrix_file()
    test_output_to_file()
    test_gap_details_structure()
    print("All trace-report tests passed.")
