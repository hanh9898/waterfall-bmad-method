#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Tests for discover-planning-artifacts.py.

Run from the skill root:
    python -m unittest scripts.tests.test_discover

Each test invokes the script as a subprocess (testing the CLI contract,
not just internals).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "discover-planning-artifacts.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


class DiscoverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.artifacts = self.root / "planning-artifacts"
        self.artifacts.mkdir()
        self.template = self.root / "templates" / "D-06_business-flow-diagram_template.md"
        self.template.parent.mkdir()
        self.template.write_text("# D-06 template\n", encoding="utf-8")
        self.out = self.root / "out.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _read_output(self) -> dict[str, object]:
        return json.loads(self.out.read_text(encoding="utf-8"))

    def test_template_missing_exits_1(self) -> None:
        bad_template = self.root / "templates" / "missing.md"
        proc = run_script(str(self.artifacts), "--template-path", str(bad_template), "-o", str(self.out))
        self.assertEqual(proc.returncode, 1, f"stderr: {proc.stderr}")
        data = self._read_output()
        self.assertEqual(data["fatal"], "template_missing")

    def test_template_present_exits_0(self) -> None:
        proc = run_script(str(self.artifacts), "--template-path", str(self.template), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        data = self._read_output()
        self.assertTrue(data["template_exists"])
        self.assertNotIn("fatal", data)

    def test_en_vi_prd_globs_match_hbc_filenames(self) -> None:
        (self.artifacts / "requirements.md").write_text("# PRD\n", encoding="utf-8")
        (self.artifacts / "yêu cầu nghiệp vụ.md").write_text("# PRD VI\n", encoding="utf-8")
        proc = run_script(str(self.artifacts), "--template-path", str(self.template), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0)
        data = self._read_output()
        prd_paths = {Path(entry["path"]).name for entry in data["prd"]}
        self.assertIn("requirements.md", prd_paths)
        self.assertIn("yêu cầu nghiệp vụ.md", prd_paths)

    def test_sharded_prd_enumerates_every_shard(self) -> None:
        prd_dir = self.artifacts / "prd"
        prd_dir.mkdir()
        (prd_dir / "index.md").write_text(
            "# PRD\n\n- [Epic 1](epics/epic-01.md)\n- [Epic 2](epics/epic-02.md)\n",
            encoding="utf-8",
        )
        epics = prd_dir / "epics"
        epics.mkdir()
        (epics / "epic-01.md").write_text("# Epic 1 — FR-001\n", encoding="utf-8")
        (epics / "epic-02.md").write_text("# Epic 2 — FR-002\n", encoding="utf-8")

        proc = run_script(str(self.artifacts), "--template-path", str(self.template), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0)
        data = self._read_output()
        self.assertEqual(len(data["prd"]), 1)
        self.assertTrue(data["prd"][0]["is_sharded"])
        shard_names = {Path(s["path"]).name for s in data["prd"][0]["shard_paths"]}
        self.assertEqual(shard_names, {"epic-01.md", "epic-02.md"})

    @unittest.skipUnless(hasattr(os, "symlink") and sys.platform != "win32", "symlinks require POSIX or admin on Windows")
    def test_symlink_is_flagged(self) -> None:
        real = self.root / "real" / "prd-real.md"
        real.parent.mkdir()
        real.write_text("# Real PRD\n", encoding="utf-8")
        link = self.artifacts / "prd-link.md"
        os.symlink(real, link)
        proc = run_script(str(self.artifacts), "--template-path", str(self.template), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0)
        data = self._read_output()
        match = next((e for e in data["prd"] if Path(e["path"]).name == "prd-link.md"), None)
        self.assertIsNotNone(match)
        self.assertTrue(match["is_symlink"])

    def test_resume_state_recommends_fresh_when_primary_absent(self) -> None:
        primary = self.artifacts / "D-06-proj-business-flow-diagram.md"  # not created
        proc = run_script(
            str(self.artifacts),
            "--template-path", str(self.template),
            "--primary", str(primary),
            "-o", str(self.out),
        )
        self.assertEqual(proc.returncode, 0)
        data = self._read_output()
        self.assertIn("resume_state", data)
        self.assertFalse(data["resume_state"]["primary_exists"])
        self.assertEqual(data["resume_state"]["recommended_intent"], "Fresh")
        # N3: discriminate "no primary" from "crashed primary" in audit log
        self.assertEqual(data["resume_state"]["fresh_reason"], "no_primary")

    def test_resume_state_recommends_resume_when_stage_1_complete(self) -> None:
        primary = self.artifacts / "D-06-proj-business-flow-diagram.md"
        primary.write_text(
            "---\nstepsCompleted: [stage-1, stage-2]\nlastStep: stage-2\nupdated: 2026-05-14\n---\n# Doc\n",
            encoding="utf-8",
        )
        proc = run_script(
            str(self.artifacts),
            "--template-path", str(self.template),
            "--primary", str(primary),
            "-o", str(self.out),
        )
        self.assertEqual(proc.returncode, 0)
        data = self._read_output()
        self.assertEqual(data["resume_state"]["recommended_intent"], "Resume")
        self.assertEqual(data["resume_state"]["primary_steps_completed"], ["stage-1", "stage-2"])

    def test_resume_state_recommends_fresh_when_steps_empty_post_crash(self) -> None:
        primary = self.artifacts / "D-06-proj-business-flow-diagram.md"
        primary.write_text(
            "---\nstepsCompleted: []\nlastStep: ''\nupdated: 2026-05-14\n---\n# Doc\n",
            encoding="utf-8",
        )
        proc = run_script(
            str(self.artifacts),
            "--template-path", str(self.template),
            "--primary", str(primary),
            "-o", str(self.out),
        )
        self.assertEqual(proc.returncode, 0)
        data = self._read_output()
        # Empty stepsCompleted = treat as crashed pre-stage-1 → Fresh, not Resume
        self.assertEqual(data["resume_state"]["recommended_intent"], "Fresh")
        # N3: fresh_reason carries the discrimination forward in the audit log
        self.assertEqual(data["resume_state"]["fresh_reason"], "crashed_no_progress")

    def test_resume_intent_no_fresh_reason_when_update(self) -> None:
        # When the intent is Update, fresh_reason must be null (no carry-over).
        primary = self.artifacts / "D-06-proj-business-flow-diagram.md"
        primary.write_text(
            "---\nstepsCompleted: [stage-1, stage-2, stage-3, stage-4, stage-5]\nlastStep: complete\nupdated: 2026-05-14\n---\n",
            encoding="utf-8",
        )
        proc = run_script(
            str(self.artifacts),
            "--template-path", str(self.template),
            "--primary", str(primary),
            "-o", str(self.out),
        )
        self.assertEqual(proc.returncode, 0)
        data = self._read_output()
        self.assertEqual(data["resume_state"]["recommended_intent"], "Update")
        self.assertIsNone(data["resume_state"]["fresh_reason"])

    def test_session_heading_regex_matches_vietnamese_log(self) -> None:
        # N5: Decision-log Session heading regex is date-anchored, so it
        # matches translated session blocks like "Phiên" or any other label.
        log = self.artifacts / ".decision-log.md"
        log.write_text(
            "---\nskill: x\n---\n\n## 2026-05-14T10:23 — Phiên: Cập nhật\n\nFlow updated.\n",
            encoding="utf-8",
        )
        primary = self.artifacts / "D-06-proj-business-flow-diagram.md"
        primary.write_text("---\nstepsCompleted: [stage-1]\n---\n", encoding="utf-8")
        proc = run_script(
            str(self.artifacts),
            "--template-path", str(self.template),
            "--primary", str(primary),
            "-o", str(self.out),
        )
        self.assertEqual(proc.returncode, 0)
        data = self._read_output()
        self.assertIsNotNone(data["resume_state"]["last_session_summary"])
        self.assertIn("Phiên", data["resume_state"]["last_session_summary"])
        self.assertIn("2026-05-14", data["resume_state"]["last_session_summary"])

    def test_prd_directory_match_uses_word_boundary(self) -> None:
        # L3: directories like "approved/" must not match the eager
        # "prd in name.lower()" check; "prd/" or "prd-customer/" still match.
        (self.artifacts / "approved").mkdir()
        (self.artifacts / "approved" / "index.md").write_text("# Approved\n", encoding="utf-8")
        (self.artifacts / "prd").mkdir()
        (self.artifacts / "prd" / "index.md").write_text("# PRD\n", encoding="utf-8")
        proc = run_script(str(self.artifacts), "--template-path", str(self.template), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0)
        data = self._read_output()
        prd_paths = {Path(entry["path"]).name for entry in data["prd"]}
        self.assertIn("prd", prd_paths)
        self.assertNotIn("approved", prd_paths)


if __name__ == "__main__":
    unittest.main()
