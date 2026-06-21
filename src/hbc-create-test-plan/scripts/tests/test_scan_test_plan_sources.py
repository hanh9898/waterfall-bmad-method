#!/usr/bin/env python3
"""Tests for scan-test-plan-sources.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).resolve().parent.parent / "scan-test-plan-sources.py")


def run_script(
    project_root: str,
    output_dir: str | None = None,
    output_file: str | None = None,
) -> subprocess.CompletedProcess:
    """Run the scan script and return the completed process."""
    cmd = [sys.executable, SCRIPT, "--project-root", project_root]
    if output_dir is not None:
        cmd.extend(["--output-dir", output_dir])
    if output_file is not None:
        cmd.extend(["-o", output_file])
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def run_and_parse(project_root: str, output_dir: str | None = None) -> dict:
    """Run the scan script and parse the JSON output."""
    result = run_script(project_root, output_dir=output_dir)
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(result.stdout)


# --- State detection tests ---


class TestFreshState:
    """Tests for fresh project state (no existing D-26)."""

    def test_empty_project_is_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = run_and_parse(tmpdir)
            assert data["state"] == "fresh"
            assert data["existing_d26"] is None
            assert data["source_count"] == 0

    def test_fresh_has_null_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = run_and_parse(tmpdir)
            assert data["d02_path"] is None
            assert data["d06_path"] is None
            assert data["framework"] is None
            assert data["project_context_path"] is None


class TestResumeState:
    """Tests for resume state (partial D-26 with lastStep != complete)."""

    def test_partial_d26_in_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            d26 = Path(tmpdir) / "D-26-test-plan.md"
            d26.write_text(
                "---\nlastStep: discovery\nversion: '0.1'\n---\n# Test Plan\n",
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir)
            assert data["state"] == "resume"
            assert data["existing_d26"]["lastStep"] == "discovery"
            assert data["existing_d26"]["version"] == "0.1"

    def test_partial_d26_in_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "_bmad-output" / "planning-artifacts"
            out_dir.mkdir(parents=True)
            d26 = out_dir / "D-26-myapp-test-plan.md"
            d26.write_text(
                "---\nlastStep: generation\nversion: '0.2'\n---\n# Test Plan\n",
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir, output_dir=str(out_dir))
            assert data["state"] == "resume"
            assert data["existing_d26"]["lastStep"] == "generation"

    def test_partial_d26_empty_laststep(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            d26 = Path(tmpdir) / "D-26-test-plan.md"
            d26.write_text("---\nversion: '0.1'\n---\n# Test Plan\n", encoding="utf-8")
            data = run_and_parse(tmpdir)
            assert data["state"] == "resume"
            assert data["existing_d26"]["lastStep"] == ""


class TestUpdateState:
    """Tests for update state (complete D-26)."""

    def test_complete_d26(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            d26 = Path(tmpdir) / "D-26-test-plan.md"
            d26.write_text(
                "---\nlastStep: complete\nversion: '1.0'\n---\n# Test Plan\n",
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir)
            assert data["state"] == "update"
            assert data["existing_d26"]["lastStep"] == "complete"
            assert data["existing_d26"]["version"] == "1.0"

    def test_complete_d26_in_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "output"
            out_dir.mkdir()
            d26 = out_dir / "D-26-app-test-plan.md"
            d26.write_text(
                "---\nlastStep: complete\nversion: '2.0'\n---\n# Test Plan\n",
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir, output_dir=str(out_dir))
            assert data["state"] == "update"


# --- Framework detection tests ---


class TestFrameworkDetection:
    """Tests for test framework detection from project config files."""

    def test_detect_jest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = Path(tmpdir) / "package.json"
            pkg.write_text(
                json.dumps({"devDependencies": {"jest": "^29.0.0"}}),
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir)
            assert data["framework"] == "jest"

    def test_detect_vitest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = Path(tmpdir) / "package.json"
            pkg.write_text(
                json.dumps({"devDependencies": {"vitest": "^1.0.0"}}),
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir)
            assert data["framework"] == "vitest"

    def test_detect_vitest_from_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = Path(tmpdir) / "package.json"
            pkg.write_text(
                json.dumps({"scripts": {"test": "vitest run"}}),
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir)
            assert data["framework"] == "vitest"

    def test_detect_pytest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            req = Path(tmpdir) / "requirements.txt"
            req.write_text("pytest>=7.0\nrequests\n", encoding="utf-8")
            data = run_and_parse(tmpdir)
            assert data["framework"] == "pytest"

    def test_detect_pytest_from_pyproject(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pyproject = Path(tmpdir) / "pyproject.toml"
            pyproject.write_text(
                '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir)
            assert data["framework"] == "pytest"

    def test_detect_go_test(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            gomod = Path(tmpdir) / "go.mod"
            gomod.write_text("module example.com/app\n\ngo 1.21\n", encoding="utf-8")
            data = run_and_parse(tmpdir)
            assert data["framework"] == "go-test"

    def test_detect_go_testify(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            gomod = Path(tmpdir) / "go.mod"
            gomod.write_text(
                "module example.com/app\n\ngo 1.21\n\nrequire github.com/stretchr/testify v1.8.0\n",
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir)
            assert data["framework"] == "testify"

    def test_detect_cargo_test(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cargo = Path(tmpdir) / "Cargo.toml"
            cargo.write_text('[package]\nname = "myapp"\nversion = "0.1.0"\n', encoding="utf-8")
            data = run_and_parse(tmpdir)
            assert data["framework"] == "cargo-test"

    def test_detect_junit_gradle(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            gradle = Path(tmpdir) / "build.gradle"
            gradle.write_text(
                "dependencies {\n    testImplementation 'org.junit.jupiter:junit-jupiter:5.9.0'\n}\n",
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir)
            assert data["framework"] == "junit"

    def test_no_framework_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty directory, no config files
            data = run_and_parse(tmpdir)
            assert data["framework"] is None

    def test_detect_mocha(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = Path(tmpdir) / "package.json"
            pkg.write_text(
                json.dumps({"devDependencies": {"mocha": "^10.0.0"}}),
                encoding="utf-8",
            )
            data = run_and_parse(tmpdir)
            assert data["framework"] == "mocha"


# --- Source document discovery tests ---


class TestSourceDiscovery:
    """Tests for discovering D-02, D-06, and project-context.md."""

    def test_finds_d02_in_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "D-02-requirements.md").write_text("# Req\n", encoding="utf-8")
            data = run_and_parse(tmpdir)
            assert data["d02_path"] == "D-02-requirements.md"
            assert data["source_count"] >= 1

    def test_finds_d06_in_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "D-06-business-flow.md").write_text("# Flow\n", encoding="utf-8")
            data = run_and_parse(tmpdir)
            assert data["d06_path"] == "D-06-business-flow.md"

    def test_finds_d02_in_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "_bmad-output" / "planning-artifacts"
            out_dir.mkdir(parents=True)
            (out_dir / "D-02-app-requirements.md").write_text("# Req\n", encoding="utf-8")
            data = run_and_parse(tmpdir, output_dir=str(out_dir))
            assert data["d02_path"] is not None
            assert "D-02" in data["d02_path"]

    def test_finds_project_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "project-context.md").write_text("# Context\n", encoding="utf-8")
            data = run_and_parse(tmpdir)
            assert data["project_context_path"] == "project-context.md"

    def test_finds_nested_project_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "docs"
            nested.mkdir()
            (nested / "project-context.md").write_text("# Context\n", encoding="utf-8")
            data = run_and_parse(tmpdir)
            assert data["project_context_path"] == "docs/project-context.md"

    def test_source_count_all_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "D-02-requirements.md").write_text("# Req\n", encoding="utf-8")
            (Path(tmpdir) / "D-06-business-flow.md").write_text("# Flow\n", encoding="utf-8")
            (Path(tmpdir) / "project-context.md").write_text("# Ctx\n", encoding="utf-8")
            data = run_and_parse(tmpdir)
            assert data["source_count"] == 3

    def test_source_count_none_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = run_and_parse(tmpdir)
            assert data["source_count"] == 0


# --- CLI behavior tests ---


class TestCLI:
    """Tests for command-line interface behavior."""

    def test_missing_project_root_fails(self) -> None:
        result = subprocess.run(
            [sys.executable, SCRIPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert result.returncode != 0

    def test_output_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "result.json"
            result = run_script(tmpdir, output_file=str(out_path))
            assert result.returncode == 0
            assert out_path.exists()
            data = json.loads(out_path.read_text(encoding="utf-8"))
            assert "state" in data
            assert "existing_d26" in data
            assert "framework" in data

    def test_always_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(tmpdir)
            assert result.returncode == 0

    def test_output_is_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(tmpdir)
            data = json.loads(result.stdout)
            expected_keys = {
                "state",
                "existing_d26",
                "d02_path",
                "d06_path",
                "framework",
                "project_context_path",
                "source_count",
            }
            assert set(data.keys()) == expected_keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
