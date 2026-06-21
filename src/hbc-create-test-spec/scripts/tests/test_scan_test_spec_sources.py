#!/usr/bin/env python3
"""Tests for scan-test-spec-sources.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "scan-test-spec-sources.py")


def run_script(
    project_root: str,
    output_dir: str | None = None,
    output_file: str | None = None,
) -> dict:
    """Run the scan script and return parsed JSON output."""
    cmd = [sys.executable, SCRIPT, "--project-root", project_root]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    if output_file:
        cmd.extend(["-o", output_file])
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if output_file:
        return json.loads(Path(output_file).read_text(encoding="utf-8"))
    return json.loads(result.stdout)


class TestFreshState:
    """Tests for fresh state detection (no existing D-27)."""

    def test_empty_project_is_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(tmpdir)
            assert result["state"] == "fresh"
            assert result["existing_d27"] is None
            assert result["source_count"] == 0
            assert result["req_ids"] == []

    def test_fresh_with_source_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "D-02-requirements.md").write_text(
                "# Requirements\nREQ-001 Login\nREQ-002 Register\n",
                encoding="utf-8",
            )
            (root / "D-26-test-plan.md").write_text(
                "# Test Plan\n", encoding="utf-8"
            )
            result = run_script(tmpdir)
            assert result["state"] == "fresh"
            assert result["existing_d27"] is None
            assert result["d02_path"] is not None
            assert result["d26_path"] is not None
            assert result["source_count"] == 2


class TestResumeState:
    """Tests for resume state detection (partial D-27)."""

    def test_partial_d27_is_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            d27 = root / "D-27-test-spec.md"
            d27.write_text(
                "---\nlastStep: discovery\nversion: '0.1'\ntc_count: '5'\n---\n# Test Spec\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir)
            assert result["state"] == "resume"
            assert result["existing_d27"] is not None
            assert result["existing_d27"]["lastStep"] == "discovery"
            assert result["existing_d27"]["version"] == "0.1"

    def test_d27_in_output_dir_is_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            out_dir = root / "_bmad-output" / "planning-artifacts"
            out_dir.mkdir(parents=True)
            d27 = out_dir / "D-27-project-test-spec.md"
            d27.write_text(
                "---\nlastStep: generation\nversion: '0.2'\n---\n# Test Spec\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir)
            assert result["state"] == "resume"
            assert result["existing_d27"]["lastStep"] == "generation"


class TestUpdateState:
    """Tests for update state detection (complete D-27)."""

    def test_complete_d27_is_update(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            d27 = root / "D-27-test-spec.md"
            d27.write_text(
                "---\nlastStep: complete\nversion: '1.0'\ntc_count: '42'\n---\n# Test Spec\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir)
            assert result["state"] == "update"
            assert result["existing_d27"]["lastStep"] == "complete"
            assert result["existing_d27"]["version"] == "1.0"


class TestReqIdExtraction:
    """Tests for REQ ID extraction from D-02."""

    def test_extracts_req_ids_from_d02(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "D-02-requirements.md").write_text(
                "# Requirements\n"
                "REQ-001 User login\n"
                "REQ-002 User registration\n"
                "REQ-010 Admin panel\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir)
            assert "REQ-001" in result["req_ids"]
            assert "REQ-002" in result["req_ids"]
            assert "REQ-010" in result["req_ids"]
            assert len(result["req_ids"]) == 3

    def test_deduplicates_req_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "D-02-requirements.md").write_text(
                "REQ-001 first mention\nREQ-001 second mention\nREQ-002 another\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir)
            assert result["req_ids"].count("REQ-001") == 1
            assert len(result["req_ids"]) == 2

    def test_no_d02_returns_empty_req_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_script(tmpdir)
            assert result["req_ids"] == []

    def test_req_ids_are_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "D-02-requirements.md").write_text(
                "REQ-003 third\nREQ-001 first\nREQ-002 second\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir)
            assert result["req_ids"] == ["REQ-001", "REQ-002", "REQ-003"]


class TestMissingProjectRoot:
    """Tests for missing or invalid project root."""

    def test_nonexistent_project_root_returns_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent = str(Path(tmpdir) / "does-not-exist")
            result = run_script(nonexistent)
            assert result["state"] == "fresh"
            assert result["existing_d27"] is None
            assert result["source_count"] == 0

    def test_always_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [sys.executable, SCRIPT, "--project-root", tmpdir]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            assert proc.returncode == 0


class TestOutputToFile:
    """Tests for -o/--output file option."""

    def test_writes_json_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "result.json"
            result = run_script(tmpdir, output_file=str(out_path))
            assert out_path.exists()
            assert "state" in result
            assert "existing_d27" in result

    def test_stdout_is_empty_when_output_file_given(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "result.json"
            cmd = [
                sys.executable, SCRIPT,
                "--project-root", tmpdir,
                "-o", str(out_path),
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            # stdout should not contain JSON (output goes to file)
            assert proc.stdout.strip() == ""


class TestTcCountParsing:
    """Tests for tc_count extraction from existing D-27 frontmatter."""

    def test_tc_count_from_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            d27 = root / "D-27-test-spec.md"
            d27.write_text(
                "---\nlastStep: complete\nversion: '1.0'\ntc_count: '42'\n---\n# Spec\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir)
            assert result["existing_d27"]["tc_count"] == "42"

    def test_tc_count_numeric_without_quotes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            d27 = root / "D-27-test-spec.md"
            d27.write_text(
                "---\nlastStep: discovery\nversion: '0.1'\ntc_count: 15\n---\n# Spec\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir)
            assert result["existing_d27"]["tc_count"] == "15"

    def test_tc_count_missing_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            d27 = root / "D-27-test-spec.md"
            d27.write_text(
                "---\nlastStep: discovery\nversion: '0.1'\n---\n# Spec\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir)
            assert result["existing_d27"]["tc_count"] is None


class TestSourceDiscovery:
    """Tests for source document discovery."""

    def test_finds_all_four_source_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "D-02-requirements.md").write_text("# Reqs\n", encoding="utf-8")
            (root / "D-06-business-flow.md").write_text("# Flow\n", encoding="utf-8")
            (root / "D-19-er-diagram.md").write_text("# ER\n", encoding="utf-8")
            (root / "D-26-test-plan.md").write_text("# Plan\n", encoding="utf-8")
            result = run_script(tmpdir)
            assert result["d02_path"] is not None
            assert result["d06_path"] is not None
            assert result["d19_path"] is not None
            assert result["d26_path"] is not None
            assert result["source_count"] == 4

    def test_finds_docs_in_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            out_dir = root / "_bmad-output" / "planning-artifacts"
            out_dir.mkdir(parents=True)
            (out_dir / "D-02-requirements.md").write_text(
                "# Reqs\nREQ-001 Login\n", encoding="utf-8"
            )
            result = run_script(tmpdir)
            assert result["d02_path"] is not None
            assert "REQ-001" in result["req_ids"]

    def test_partial_source_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "D-02-requirements.md").write_text("# Reqs\n", encoding="utf-8")
            result = run_script(tmpdir)
            assert result["d02_path"] is not None
            assert result["d06_path"] is None
            assert result["d19_path"] is None
            assert result["d26_path"] is None
            assert result["source_count"] == 1

    def test_custom_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            custom_dir = root / "custom" / "output"
            custom_dir.mkdir(parents=True)
            (custom_dir / "D-27-test-spec.md").write_text(
                "---\nlastStep: complete\nversion: '1.0'\n---\n# Spec\n",
                encoding="utf-8",
            )
            result = run_script(tmpdir, output_dir=str(custom_dir))
            assert result["state"] == "update"
            assert result["existing_d27"] is not None
