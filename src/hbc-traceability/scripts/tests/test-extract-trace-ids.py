#!/usr/bin/env python3
"""Tests for extract-trace-ids.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "extract-trace-ids.py")


def run(source: str, pattern: str, project_root: str) -> dict:
    result = subprocess.run(
        [sys.executable, SCRIPT, "--source", source, "--pattern", pattern, "--project-root", project_root],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else {"error": result.stderr}


def test_extract_req_ids():
    with tempfile.TemporaryDirectory() as tmp:
        doc = Path(tmp) / "D-02-requirements.md"
        doc.write_text("# Requirements\n\n- REQ-001 Login\n- REQ-002 Dashboard\n- REQ-003 Reports\n")
        result = run("D-02-*", r"REQ-\d{3}", tmp)
        assert result["status"] == "OK"
        assert result["unique_count"] == 3
        assert "REQ-001" in result["ids"]
        assert "REQ-003" in result["ids"]


def test_extract_tc_ids():
    with tempfile.TemporaryDirectory() as tmp:
        doc = Path(tmp) / "D-27-test-spec.md"
        doc.write_text("| TC-001 | Login success |\n| TC-002 | Login failure |\n| TC-001 | duplicate |\n")
        result = run("D-27-*", r"TC-\d{3}", tmp)
        assert result["status"] == "OK"
        assert result["unique_count"] == 2
        assert result["total_found"] == 3


def test_no_files_found():
    with tempfile.TemporaryDirectory() as tmp:
        result = run("nonexistent-*", r"REQ-\d{3}", tmp)
        assert result["status"] == "NO_FILES"
        assert result["ids"] == []


def test_no_matches_in_file():
    with tempfile.TemporaryDirectory() as tmp:
        doc = Path(tmp) / "D-02-empty.md"
        doc.write_text("# No requirement IDs here\nJust plain text.\n")
        result = run("D-02-*", r"REQ-\d{3}", tmp)
        assert result["status"] == "NO_MATCHES"
        assert result["unique_count"] == 0


def test_multiple_files():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "D-02-part1.md").write_text("REQ-001 REQ-002\n")
        (Path(tmp) / "D-02-part2.md").write_text("REQ-003 REQ-001\n")
        result = run("D-02-*", r"REQ-\d{3}", tmp)
        assert result["status"] == "OK"
        assert result["unique_count"] == 3
        assert result["file_count"] == 2


def test_output_to_file():
    with tempfile.TemporaryDirectory() as tmp:
        doc = Path(tmp) / "D-02-test.md"
        doc.write_text("REQ-001\n")
        out = Path(tmp) / "output.json"
        subprocess.run(
            [sys.executable, SCRIPT, "--source", "D-02-*", "--pattern", r"REQ-\d{3}",
             "--project-root", tmp, "-o", str(out)],
            capture_output=True, text=True,
        )
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["status"] == "OK"


if __name__ == "__main__":
    test_extract_req_ids()
    test_extract_tc_ids()
    test_no_files_found()
    test_no_matches_in_file()
    test_multiple_files()
    test_output_to_file()
    print("All extract-trace-ids tests passed.")
