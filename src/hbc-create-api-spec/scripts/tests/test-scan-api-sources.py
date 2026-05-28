#!/usr/bin/env python3
"""Tests for scan-api-sources.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "scan_api_sources",
    os.path.join(os.path.dirname(__file__), "..", "scan-api-sources.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

scan = mod.scan
detect_framework = mod.detect_framework
detect_needs_api = mod.detect_needs_api
find_artifact = mod.find_artifact


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class TestScanFresh:
    def test_empty_output_dir(self, tmp_path):
        output_dir = tmp_path / "design"
        output_dir.mkdir()
        result = scan(str(tmp_path), str(output_dir))
        assert result["state"] == "fresh"
        assert result["existing_d21"] is None

    def test_nonexistent_output_dir(self, tmp_path):
        result = scan(str(tmp_path), str(tmp_path / "nonexistent"))
        assert result["state"] == "fresh"
        assert result["existing_d21"] is None


class TestScanResume:
    def test_partial_d21(self, tmp_path):
        output_dir = tmp_path / "design"
        output_dir.mkdir()
        _write(
            str(output_dir / "D-21-test-api-spec.md"),
            "---\nlastStep: discovery\n---\n# Test",
        )
        result = scan(str(tmp_path), str(output_dir))
        assert result["state"] == "resume"
        assert result["existing_d21"]["file"] == "D-21-test-api-spec.md"


class TestScanUpdate:
    def test_complete_d21(self, tmp_path):
        output_dir = tmp_path / "design"
        output_dir.mkdir()
        _write(
            str(output_dir / "D-21-test-api-spec.md"),
            "---\nlastStep: complete\n---\n# Test",
        )
        result = scan(str(tmp_path), str(output_dir))
        assert result["state"] == "update"


class TestScanSkip:
    def test_odoo_no_api(self, tmp_path):
        output_dir = tmp_path / "design"
        output_dir.mkdir()
        _write(
            str(tmp_path / "project-context.md"),
            "# Project\nFramework: Odoo 16\nInternal module using _inherit.",
        )
        result = scan(str(tmp_path), str(output_dir))
        assert result["state"] == "skip"
        assert result["needs_api"] is False


class TestDetectFramework:
    def test_django(self, tmp_path):
        _write(str(tmp_path / "project-context.md"), "# Project\nFramework: Django 4.2\nUses manage.py")
        assert detect_framework(str(tmp_path)) == "django"

    def test_no_context(self, tmp_path):
        assert detect_framework(str(tmp_path)) is None


class TestDetectNeedsApi:
    def test_odoo_false(self, tmp_path):
        assert detect_needs_api(str(tmp_path), "odoo") is False

    def test_api_indicators(self, tmp_path):
        _write(str(tmp_path / "project-context.md"), "REST API with endpoints and swagger docs")
        assert detect_needs_api(str(tmp_path), "django") is True

    def test_no_indicators(self, tmp_path):
        _write(str(tmp_path / "project-context.md"), "Simple batch processing job.")
        assert detect_needs_api(str(tmp_path), "django") is False

    def test_no_context_none(self, tmp_path):
        assert detect_needs_api(str(tmp_path), "django") is None


class TestFindArtifact:
    def test_finds_d02(self, tmp_path):
        design_dir = tmp_path / "design"
        plan_dir = tmp_path / "plan"
        design_dir.mkdir()
        plan_dir.mkdir()
        _write(str(plan_dir / "D-02-requirements.md"), "# D-02")
        result = find_artifact(str(design_dir), "D-02")
        assert result is not None
        assert "D-02-requirements.md" in result

    def test_not_found(self, tmp_path):
        design_dir = tmp_path / "design"
        design_dir.mkdir()
        assert find_artifact(str(design_dir), "D-02") is None


class TestCLI:
    def test_cli_json_output(self, tmp_path):
        import subprocess

        output_dir = tmp_path / "design"
        output_dir.mkdir()

        script = os.path.join(
            os.path.dirname(__file__), "..", "scan-api-sources.py"
        )
        result = subprocess.run(
            [
                sys.executable, script,
                "--project-root", str(tmp_path),
                "--output-dir", str(output_dir),
            ],
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["state"] == "fresh"
