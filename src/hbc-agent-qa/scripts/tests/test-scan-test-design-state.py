#!/usr/bin/env python3
"""Tests for scan-test-design-state.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "scan_test_design_state",
    os.path.join(os.path.dirname(__file__), "..", "scan-test-design-state.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

scan = mod.scan
read_frontmatter_date = mod.read_frontmatter_date


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class TestAllMissing:
    def test_empty_dir_returns_blocked(self, tmp_path):
        result = scan(str(tmp_path))
        assert result["status"] == "blocked"
        assert result["next_recommended"] == "D-26"
        for v in result["test_design_state"].values():
            assert v["exists"] is False
            assert v["path"] is None


class TestPartialArtifacts:
    def test_only_d26_exists(self, tmp_path):
        _write(str(tmp_path / "D-26-test-plan.md"))
        result = scan(str(tmp_path))
        assert result["status"] == "blocked"
        assert result["test_design_state"]["D-26"]["exists"] is True
        assert result["test_design_state"]["D-26"]["path"].endswith("D-26-test-plan.md")
        assert result["next_recommended"] == "D-27"

    def test_d26_and_d27_exist(self, tmp_path):
        _write(str(tmp_path / "D-26-plan.md"))
        _write(str(tmp_path / "D-27-spec.md"))
        result = scan(str(tmp_path))
        assert result["status"] == "complete"
        assert result["next_recommended"] == "PG"


class TestFrontmatterDate:
    def test_extracts_date(self, tmp_path):
        path = str(tmp_path / "D-26-plan.md")
        _write(path, "---\nupdated: 2026-05-28\n---\n# Plan")
        assert read_frontmatter_date(path) == "2026-05-28"

    def test_no_frontmatter(self, tmp_path):
        path = str(tmp_path / "D-27-spec.md")
        _write(path, "# No frontmatter")
        assert read_frontmatter_date(path) is None


class TestCLI:
    def test_cli_json_output(self, tmp_path):
        import subprocess

        _write(str(tmp_path / "D-26-plan.md"))
        script = os.path.join(os.path.dirname(__file__), "..", "scan-test-design-state.py")
        result = subprocess.run(
            [sys.executable, script, str(tmp_path)],
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "blocked"
        assert data["test_design_state"]["D-26"]["exists"] is True

    def test_cli_nonexistent_dir(self, tmp_path):
        import subprocess

        script = os.path.join(os.path.dirname(__file__), "..", "scan-test-design-state.py")
        result = subprocess.run(
            [sys.executable, script, str(tmp_path / "nope")],
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "blocked"
        assert data["next_recommended"] == "D-26"
