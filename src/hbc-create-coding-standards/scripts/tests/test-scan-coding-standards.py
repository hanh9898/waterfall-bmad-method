#!/usr/bin/env python3
"""Tests for scan-coding-standards.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "scan_coding_standards",
    os.path.join(os.path.dirname(__file__), "..", "scan-coding-standards.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

scan = mod.scan
detect_framework = mod.detect_framework
read_frontmatter = mod.read_frontmatter
find_project_context = mod.find_project_context


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
        assert result["existing_d12"] is None

    def test_nonexistent_output_dir(self, tmp_path):
        result = scan(str(tmp_path), str(tmp_path / "nonexistent"))
        assert result["state"] == "fresh"
        assert result["existing_d12"] is None


class TestScanResume:
    def test_partial_d12_detected(self, tmp_path):
        output_dir = tmp_path / "design"
        output_dir.mkdir()
        _write(
            str(output_dir / "D-12-test-coding-standards.md"),
            "---\nlastStep: discovery\nversion: '1.0'\n---\n# Test",
        )
        result = scan(str(tmp_path), str(output_dir))
        assert result["state"] == "resume"
        assert result["existing_d12"]["file"] == "D-12-test-coding-standards.md"
        assert result["existing_d12"]["frontmatter"]["lastStep"] == "discovery"


class TestScanUpdate:
    def test_complete_d12_detected(self, tmp_path):
        output_dir = tmp_path / "design"
        output_dir.mkdir()
        _write(
            str(output_dir / "D-12-test-coding-standards.md"),
            "---\nlastStep: complete\nversion: '1.0'\n---\n# Test",
        )
        result = scan(str(tmp_path), str(output_dir))
        assert result["state"] == "update"
        assert result["existing_d12"]["frontmatter"]["lastStep"] == "complete"


class TestDetectFramework:
    def test_odoo_detected(self, tmp_path):
        ctx = str(tmp_path / "project-context.md")
        _write(ctx, "# Project\nFramework: Odoo 16\nUses _inherit and @api.model")
        assert detect_framework(ctx) == "odoo"

    def test_django_detected(self, tmp_path):
        ctx = str(tmp_path / "project-context.md")
        _write(ctx, "# Project\nFramework: Django 4.2\nUses manage.py and settings.py")
        assert detect_framework(ctx) == "django"

    def test_nextjs_detected(self, tmp_path):
        ctx = str(tmp_path / "project-context.md")
        _write(ctx, "# Project\nFramework: Next.js 14\nApp Router with server components")
        assert detect_framework(ctx) == "nextjs"

    def test_react_detected(self, tmp_path):
        ctx = str(tmp_path / "project-context.md")
        _write(ctx, "# Project\nFramework: React with TSX\nVite bundler, JSX components")
        assert detect_framework(ctx) == "react"

    def test_no_framework(self, tmp_path):
        ctx = str(tmp_path / "project-context.md")
        _write(ctx, "# Project\nGeneric backend service.")
        assert detect_framework(ctx) is None

    def test_missing_file(self):
        assert detect_framework("/nonexistent/path.md") is None

    def test_none_path(self):
        assert detect_framework(None) is None


class TestFindProjectContext:
    def test_root_level(self, tmp_path):
        _write(str(tmp_path / "project-context.md"), "# Context")
        found = find_project_context(str(tmp_path))
        assert found is not None
        assert found.endswith("project-context.md")

    def test_bmad_level(self, tmp_path):
        _write(str(tmp_path / "_bmad" / "project-context.md"), "# Context")
        found = find_project_context(str(tmp_path))
        assert found is not None

    def test_not_found(self, tmp_path):
        found = find_project_context(str(tmp_path))
        assert found is None


class TestReadFrontmatter:
    def test_extracts_fields(self, tmp_path):
        path = str(tmp_path / "doc.md")
        _write(path, "---\ntitle: Test\nversion: '1.0'\nlastStep: complete\n---\n# Content")
        fm = read_frontmatter(path)
        assert fm["title"] == "Test"
        assert fm["version"] == "1.0"
        assert fm["lastStep"] == "complete"

    def test_no_frontmatter(self, tmp_path):
        path = str(tmp_path / "doc.md")
        _write(path, "# No frontmatter")
        fm = read_frontmatter(path)
        assert fm == {}

    def test_missing_file(self):
        fm = read_frontmatter("/nonexistent/file.md")
        assert fm == {}


class TestCLI:
    def test_cli_json_output(self, tmp_path):
        import subprocess

        output_dir = tmp_path / "design"
        output_dir.mkdir()
        _write(
            str(output_dir / "D-12-test.md"),
            "---\nlastStep: complete\n---\n# Test",
        )

        script = os.path.join(
            os.path.dirname(__file__), "..", "scan-coding-standards.py"
        )
        result = subprocess.run(
            [
                sys.executable,
                script,
                "--project-root",
                str(tmp_path),
                "--output-dir",
                str(output_dir),
            ],
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["state"] == "update"

    def test_cli_file_output(self, tmp_path):
        import subprocess

        output_dir = tmp_path / "design"
        output_dir.mkdir()
        out_file = str(tmp_path / "result.json")

        script = os.path.join(
            os.path.dirname(__file__), "..", "scan-coding-standards.py"
        )
        result = subprocess.run(
            [
                sys.executable,
                script,
                "--project-root",
                str(tmp_path),
                "--output-dir",
                str(output_dir),
                "-o",
                out_file,
            ],
            capture_output=True,
        )
        assert result.returncode == 0
        with open(out_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["state"] == "fresh"
