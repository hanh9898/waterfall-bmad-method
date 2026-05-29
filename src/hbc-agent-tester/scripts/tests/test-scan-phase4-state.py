#!/usr/bin/env python3
"""Tests for scan-phase4-state.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "scan_phase4_state",
    os.path.join(os.path.dirname(__file__), "..", "scan-phase4-state.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

scan = mod.scan
read_frontmatter_date = mod.read_frontmatter_date
read_acceptance_decision = mod.read_acceptance_decision


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class TestReadFrontmatterDate:
    def test_with_date(self, tmp_path):
        path = str(tmp_path / "doc.md")
        _write(path, "---\ntitle: Test\nupdated: 2026-05-28\n---\n\n# Doc")
        assert read_frontmatter_date(path) == "2026-05-28"

    def test_no_frontmatter(self, tmp_path):
        path = str(tmp_path / "doc.md")
        _write(path, "# Just a doc")
        assert read_frontmatter_date(path) is None

    def test_file_not_found(self):
        assert read_frontmatter_date("/nonexistent/file.md") is None


class TestReadAcceptanceDecision:
    def test_accepted(self, tmp_path):
        path = str(tmp_path / "acceptance.md")
        _write(path, '---\ndecision: "ACCEPTED"\n---\n')
        assert read_acceptance_decision(path) == "ACCEPTED"

    def test_rejected(self, tmp_path):
        path = str(tmp_path / "acceptance.md")
        _write(path, "---\ndecision: REJECTED\n---\n")
        assert read_acceptance_decision(path) == "REJECTED"

    def test_no_decision(self, tmp_path):
        path = str(tmp_path / "acceptance.md")
        _write(path, "# No decision\n")
        assert read_acceptance_decision(path) is None


class TestScan:
    def test_empty_directory(self, tmp_path):
        result = scan(str(tmp_path))
        assert result["status"] == "blocked"
        assert result["next_recommended"] == "TE"
        assert not result["testing_state"]["test-execution-report"]["exists"]

    def test_only_execution_report(self, tmp_path):
        _write(
            str(tmp_path / "test-execution-report.md"),
            "---\nexecuted_at: 2026-05-28\n---\n# Report",
        )
        result = scan(str(tmp_path))
        assert result["status"] == "blocked"
        assert result["next_recommended"] == "AC"
        assert result["testing_state"]["test-execution-report"]["exists"]

    def test_both_with_accepted(self, tmp_path):
        _write(
            str(tmp_path / "test-execution-report.md"),
            "---\nexecuted_at: 2026-05-28\n---\n# Report",
        )
        _write(
            str(tmp_path / "acceptance-report.md"),
            '---\ndecision: "ACCEPTED"\ndecided_at: 2026-05-28\n---\n# Acceptance',
        )
        result = scan(str(tmp_path))
        assert result["status"] == "complete"
        assert result["acceptance_decision"] == "ACCEPTED"
        assert result["next_recommended"] == "PG"

    def test_both_with_rejected(self, tmp_path):
        _write(
            str(tmp_path / "test-execution-report.md"),
            "---\nexecuted_at: 2026-05-28\n---\n# Report",
        )
        _write(
            str(tmp_path / "acceptance-report.md"),
            '---\ndecision: "REJECTED"\n---\n# Acceptance',
        )
        result = scan(str(tmp_path))
        assert result["status"] == "blocked"
        assert result["acceptance_decision"] == "REJECTED"

    def test_cli_exit_always_zero(self, tmp_path):
        import subprocess

        script = os.path.join(os.path.dirname(__file__), "..", "scan-phase4-state.py")
        result = subprocess.run(
            [sys.executable, script, str(tmp_path)], capture_output=True
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "blocked"

    def test_cli_nonexistent_dir(self):
        import subprocess

        script = os.path.join(os.path.dirname(__file__), "..", "scan-phase4-state.py")
        result = subprocess.run(
            [sys.executable, script, "/nonexistent/path"], capture_output=True
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "blocked"
