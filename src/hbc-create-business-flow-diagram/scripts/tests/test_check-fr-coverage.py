#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Tests for check-fr-coverage.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "check-fr-coverage.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class CheckFrCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "out.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _result(self) -> dict[str, object]:
        return json.loads(self.out.read_text(encoding="utf-8"))

    def test_full_coverage_passes(self) -> None:
        prd = self.root / "prd.md"
        prd.write_text("# PRD\n- FR-001 Login\n- FR-002 Logout\n", encoding="utf-8")
        d06 = self.root / "d06.md"
        d06.write_text("# Flows\nFlow for FR-001 and FR-002.\n", encoding="utf-8")

        proc = run_script("--prd", str(prd), "--d06", str(d06), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        result = self._result()
        self.assertTrue(result["passed"])
        self.assertEqual(set(result["covered"]), {"FR-001", "FR-002"})
        self.assertEqual(result["uncovered"], [])
        self.assertEqual(result["phantom"], [])

    def test_uncovered_fr_flagged(self) -> None:
        prd = self.root / "prd.md"
        prd.write_text("# PRD\nFR-001, FR-002, FR-003\n", encoding="utf-8")
        d06 = self.root / "d06.md"
        d06.write_text("# Flow\nFR-001 only\n", encoding="utf-8")

        proc = run_script("--prd", str(prd), "--d06", str(d06), "-o", str(self.out))
        self.assertEqual(proc.returncode, 1)
        result = self._result()
        self.assertFalse(result["passed"])
        self.assertEqual(set(result["uncovered"]), {"FR-002", "FR-003"})

    def test_phantom_fr_flagged(self) -> None:
        prd = self.root / "prd.md"
        prd.write_text("FR-001\n", encoding="utf-8")
        d06 = self.root / "d06.md"
        d06.write_text("FR-001 and FR-999 (typo)\n", encoding="utf-8")

        proc = run_script("--prd", str(prd), "--d06", str(d06), "-o", str(self.out))
        self.assertEqual(proc.returncode, 1)
        result = self._result()
        self.assertEqual(result["phantom"], ["FR-999"])

    def test_nfr_identifiers_extracted(self) -> None:
        prd = self.root / "prd.md"
        prd.write_text("NFR-007 Latency\nFR-1.2 Login submit\n", encoding="utf-8")
        d06 = self.root / "d06.md"
        d06.write_text("NFR-007 and FR-1.2\n", encoding="utf-8")

        proc = run_script("--prd", str(prd), "--d06", str(d06), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0)
        result = self._result()
        self.assertEqual(set(result["covered"]), {"NFR-007", "FR-1.2"})

    def test_excluded_dirs_skipped_in_directory_mode(self) -> None:
        prd_dir = self.root / "prd"
        prd_dir.mkdir()
        (prd_dir / "current.md").write_text("# PRD current\nFR-001\nFR-002\n", encoding="utf-8")
        (prd_dir / "archive").mkdir()
        (prd_dir / "archive" / "v0.9.md").write_text("# Old PRD\nFR-999 (retired)\n", encoding="utf-8")
        (prd_dir / "notes").mkdir()
        (prd_dir / "notes" / "scratch.md").write_text("FR-888\n", encoding="utf-8")

        d06 = self.root / "d06.md"
        d06.write_text("Flows for FR-001 and FR-002\n", encoding="utf-8")

        proc = run_script("--prd", str(prd_dir), "--d06", str(d06), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        result = self._result()
        self.assertTrue(result["passed"])
        # FR-999 and FR-888 from excluded dirs should NOT appear anywhere
        self.assertNotIn("FR-999", result["covered"] + result["uncovered"] + result["phantom"])
        self.assertNotIn("FR-888", result["covered"] + result["uncovered"] + result["phantom"])

    def test_multiple_prd_paths_aggregated(self) -> None:
        prd1 = self.root / "prd1.md"
        prd1.write_text("FR-001\n", encoding="utf-8")
        prd2 = self.root / "prd2.md"
        prd2.write_text("FR-002\n", encoding="utf-8")
        d06 = self.root / "d06.md"
        d06.write_text("FR-001 and FR-002\n", encoding="utf-8")

        proc = run_script("--prd", str(prd1), "--prd", str(prd2), "--d06", str(d06), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0)
        result = self._result()
        self.assertEqual(set(result["covered"]), {"FR-001", "FR-002"})

    def test_missing_d06_returns_error_exit_2(self) -> None:
        prd = self.root / "prd.md"
        prd.write_text("FR-001\n", encoding="utf-8")
        proc = run_script("--prd", str(prd), "--d06", str(self.root / "missing.md"), "-o", str(self.out))
        self.assertEqual(proc.returncode, 2)
        result = self._result()
        self.assertEqual(result["error"], "d06_missing")


if __name__ == "__main__":
    unittest.main()
