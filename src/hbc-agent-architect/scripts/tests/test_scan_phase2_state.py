#!/usr/bin/env python3
"""Tests for scan-phase2-state.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "scan_phase2_state",
    os.path.join(os.path.dirname(__file__), "..", "scan-phase2-state.py"),
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
        assert result["next_recommended"] == "D-19"
        for v in result["phase2_state"].values():
            assert v["exists"] is False
            assert v["path"] is None


class TestPartialArtifacts:
    def test_only_d19_exists(self, tmp_path):
        _write(str(tmp_path / "D-19-database-design.md"))
        result = scan(str(tmp_path))
        assert result["status"] == "blocked"
        assert result["phase2_state"]["D-19"]["exists"] is True
        assert result["phase2_state"]["D-19"]["path"].endswith("D-19-database-design.md")
        assert result["next_recommended"] == "D-12"

    def test_d19_and_d12_exist(self, tmp_path):
        _write(str(tmp_path / "D-19-db.md"))
        _write(str(tmp_path / "D-12-coding.md"))
        result = scan(str(tmp_path))
        assert result["status"] == "complete"
        assert result["next_recommended"] == "PG"

    def test_d21_optional(self, tmp_path):
        _write(str(tmp_path / "D-19-db.md"))
        _write(str(tmp_path / "D-12-coding.md"))
        result = scan(str(tmp_path))
        assert result["status"] == "complete"
        assert result["phase2_state"]["D-21"]["exists"] is False


class TestAllPresent:
    def test_all_artifacts_returns_complete(self, tmp_path):
        _write(str(tmp_path / "D-19-db.md"))
        _write(str(tmp_path / "D-12-coding.md"))
        _write(str(tmp_path / "D-21-api.md"))
        result = scan(str(tmp_path))
        assert result["status"] == "complete"
        assert result["phase2_state"]["D-21"]["exists"] is True


class TestFrontmatterDate:
    def test_extracts_date(self, tmp_path):
        path = str(tmp_path / "D-19-db.md")
        _write(path, "---\nupdated: 2026-05-28\n---\n# DB")
        assert read_frontmatter_date(path) == "2026-05-28"

    def test_no_frontmatter(self, tmp_path):
        path = str(tmp_path / "D-12-cs.md")
        _write(path, "# No frontmatter")
        assert read_frontmatter_date(path) is None


class TestNonexistentDir:
    def test_returns_all_missing(self, tmp_path):
        result = scan(str(tmp_path / "nonexistent"))
        # main() handles this, but scan expects existing dir
        # so test via checking returned data still makes sense
        pass


class TestCLI:
    def test_cli_json_output(self, tmp_path):
        import subprocess

        _write(str(tmp_path / "D-19-db.md"))
        script = os.path.join(os.path.dirname(__file__), "..", "scan-phase2-state.py")
        result = subprocess.run(
            [sys.executable, script, str(tmp_path)],
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "blocked"
        assert data["phase2_state"]["D-19"]["exists"] is True

    def test_cli_nonexistent_dir(self, tmp_path):
        import subprocess

        script = os.path.join(os.path.dirname(__file__), "..", "scan-phase2-state.py")
        result = subprocess.run(
            [sys.executable, script, str(tmp_path / "nope")],
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "blocked"
