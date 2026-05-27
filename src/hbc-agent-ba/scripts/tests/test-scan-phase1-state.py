#!/usr/bin/env python3
"""Tests for scan-phase1-state.py."""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "scan_phase1_state",
    os.path.join(os.path.dirname(__file__), "..", "scan-phase1-state.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

scan = mod.scan
read_frontmatter_date = mod.read_frontmatter_date


@pytest.fixture
def tmp_output(tmp_path):
    return tmp_path


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class TestDirectoryNotFound:
    def test_nonexistent_dir_returns_all_missing(self, tmp_path):
        result = mod.scan(str(tmp_path / "nonexistent"))
        assert result["status"] == "blocked"
        for v in result["phase1_state"].values():
            assert v["exists"] is False


class TestAllMissing:
    def test_empty_dir_returns_blocked(self, tmp_output):
        result = scan(str(tmp_output))
        assert result["status"] == "blocked"
        assert result["next_recommended"] == "D-02"
        assert "D-02" in result["reason"]
        for v in result["phase1_state"].values():
            assert v["exists"] is False
            assert v["file"] is None
            assert v["updated"] is None


class TestPartialArtifacts:
    def test_only_d02_exists(self, tmp_output):
        _write(str(tmp_output / "D-02-requirements.md"))
        result = scan(str(tmp_output))
        assert result["status"] == "blocked"
        assert result["phase1_state"]["D-02"]["exists"] is True
        assert result["phase1_state"]["D-02"]["file"] == "D-02-requirements.md"
        assert result["phase1_state"]["D-03"]["exists"] is False
        assert result["phase1_state"]["D-06"]["exists"] is False
        assert result["next_recommended"] == "D-03"

    def test_d02_and_d03_exist(self, tmp_output):
        _write(str(tmp_output / "D-02-requirements.md"))
        _write(str(tmp_output / "D-03-glossary.md"))
        result = scan(str(tmp_output))
        assert result["status"] == "blocked"
        assert result["next_recommended"] == "D-06"
        assert "D-06" in result["reason"]

    def test_d02_and_d06_exist_missing_d03(self, tmp_output):
        _write(str(tmp_output / "D-02-requirements.md"))
        _write(str(tmp_output / "D-06-business-flow.md"))
        result = scan(str(tmp_output))
        assert result["status"] == "blocked"
        assert result["next_recommended"] == "D-03"


class TestAllPresent:
    def test_all_core_artifacts_returns_complete(self, tmp_output):
        _write(str(tmp_output / "D-02-requirements.md"))
        _write(str(tmp_output / "D-03-glossary.md"))
        _write(str(tmp_output / "D-06-business-flow.md"))
        result = scan(str(tmp_output))
        assert result["status"] == "complete"
        assert result["next_recommended"] == "PG"
        assert "gate" in result["reason"].lower()

    def test_gate_artifact_detected(self, tmp_output):
        _write(str(tmp_output / "D-02-req.md"))
        _write(str(tmp_output / "D-03-glo.md"))
        _write(str(tmp_output / "D-06-bf.md"))
        _write(str(tmp_output / "phase-1-gate-report.md"))
        result = scan(str(tmp_output))
        assert result["phase1_state"]["phase-1-gate"]["exists"] is True


class TestFrontmatterDate:
    def test_extracts_updated_date(self, tmp_output):
        content = "---\nupdated: 2026-05-25\ntitle: Test\n---\n# Content"
        path = str(tmp_output / "D-02-requirements.md")
        _write(path, content)
        assert read_frontmatter_date(path) == "2026-05-25"

    def test_extracts_last_touched_date(self, tmp_output):
        content = "---\nlast_touched: 2026-05-20\n---\n# Content"
        path = str(tmp_output / "D-03-glossary.md")
        _write(path, content)
        assert read_frontmatter_date(path) == "2026-05-20"

    def test_no_frontmatter_returns_none(self, tmp_output):
        path = str(tmp_output / "D-06-bf.md")
        _write(path, "# No frontmatter")
        assert read_frontmatter_date(path) is None

    def test_no_date_in_frontmatter_returns_none(self, tmp_output):
        content = "---\ntitle: Test\n---\n# Content"
        path = str(tmp_output / "D-02-req.md")
        _write(path, content)
        assert read_frontmatter_date(path) is None

    def test_date_integrated_in_scan(self, tmp_output):
        _write(
            str(tmp_output / "D-02-req.md"),
            "---\nupdated: 2026-05-25\n---\n# Req",
        )
        _write(str(tmp_output / "D-03-glo.md"))
        _write(str(tmp_output / "D-06-bf.md"))
        result = scan(str(tmp_output))
        assert result["phase1_state"]["D-02"]["updated"] == "2026-05-25"
        assert result["phase1_state"]["D-03"]["updated"] is None


class TestNextRecommendedOrdering:
    def test_missing_order_is_d02_d03_d06(self, tmp_output):
        result = scan(str(tmp_output))
        assert result["next_recommended"] == "D-02"

    def test_d02_present_recommends_d03(self, tmp_output):
        _write(str(tmp_output / "D-02-req.md"))
        result = scan(str(tmp_output))
        assert result["next_recommended"] == "D-03"

    def test_d02_d03_present_recommends_d06(self, tmp_output):
        _write(str(tmp_output / "D-02-req.md"))
        _write(str(tmp_output / "D-03-glo.md"))
        result = scan(str(tmp_output))
        assert result["next_recommended"] == "D-06"

    def test_all_present_recommends_pg(self, tmp_output):
        _write(str(tmp_output / "D-02-req.md"))
        _write(str(tmp_output / "D-03-glo.md"))
        _write(str(tmp_output / "D-06-bf.md"))
        result = scan(str(tmp_output))
        assert result["next_recommended"] == "PG"


class TestOutputToFile:
    def test_writes_json_to_file(self, tmp_output):
        scan_dir = tmp_output / "artifacts"
        scan_dir.mkdir()
        out_file = str(tmp_output / "result.json")
        _write(str(scan_dir / "D-02-req.md"))

        import subprocess

        script = os.path.join(
            os.path.dirname(__file__), "..", "scan-phase1-state.py"
        )
        result = subprocess.run(
            [sys.executable, script, str(scan_dir), "-o", out_file],
            capture_output=True,
        )
        assert result.returncode == 1
        with open(out_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["status"] == "blocked"
        assert data["phase1_state"]["D-02"]["exists"] is True
