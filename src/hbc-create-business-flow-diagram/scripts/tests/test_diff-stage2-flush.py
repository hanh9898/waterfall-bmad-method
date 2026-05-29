"""Tests for diff-stage2-flush.py — scope-of-change classification."""
from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import unittest
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "diff-stage2-flush.py")


def _run(primary_text: str, log_text: str, tmp_path: Path) -> dict:
    primary = tmp_path / "D-06-business-flow-diagram.md"
    log = tmp_path / ".decision-log.md"
    out = tmp_path / "scope-diff.json"
    primary.write_text(primary_text, encoding="utf-8")
    log.write_text(log_text, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, SCRIPT, str(primary), str(log), "-o", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return json.loads(out.read_text(encoding="utf-8"))


class DiffStage2FlushTests(unittest.TestCase):
    def setUp(self) -> None:
        import tempfile
        self._tmp = tempfile.mkdtemp()
        self.tmp = Path(self._tmp)

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_identical_arrays_returns_polish(self) -> None:
        primary = textwrap.dedent("""\
            ---
            stage_2_actors: [User, System, Admin]
            stage_2_flows: [Login, Checkout]
            ---
            # Content
        """)
        log = textwrap.dedent("""\
            ## 2026-05-28T10:00 — Session: Create

            ### Discovery snapshot (Stage 2 flush)
            - **Actors:** User, System, Admin
            - **Flow inventory:**
            - **Login** — user authentication
            - **Checkout** — purchase flow
        """)
        data = _run(primary, log, self.tmp)
        self.assertEqual(data["scope"], "polish")
        self.assertFalse(data["actors_changed"])
        self.assertFalse(data["flows_changed"])

    def test_different_actors_returns_semantic(self) -> None:
        primary = textwrap.dedent("""\
            ---
            stage_2_actors: [User, System, Admin, PaymentGateway]
            stage_2_flows: [Login, Checkout]
            ---
            # Content
        """)
        log = textwrap.dedent("""\
            ## 2026-05-28T10:00 — Session: Create

            ### Discovery snapshot (Stage 2 flush)
            - **Actors:** User, System, Admin
            - **Flow inventory:**
            - **Login** — user authentication
            - **Checkout** — purchase flow
        """)
        data = _run(primary, log, self.tmp)
        self.assertEqual(data["scope"], "semantic")
        self.assertTrue(data["actors_changed"])
        self.assertFalse(data["flows_changed"])

    def test_different_flows_returns_semantic(self) -> None:
        primary = textwrap.dedent("""\
            ---
            stage_2_actors: [User, System]
            stage_2_flows: [Login, Checkout, Returns]
            ---
            # Content
        """)
        log = textwrap.dedent("""\
            ## 2026-05-28T10:00 — Session: Create

            ### Discovery snapshot (Stage 2 flush)
            - **Actors:** User, System
            - **Flow inventory:**
            - **Login** — user authentication
            - **Checkout** — purchase flow
        """)
        data = _run(primary, log, self.tmp)
        self.assertEqual(data["scope"], "semantic")
        self.assertFalse(data["actors_changed"])
        self.assertTrue(data["flows_changed"])

    def test_missing_primary_returns_exit_2(self) -> None:
        log = self.tmp / ".decision-log.md"
        log.write_text("# log", encoding="utf-8")
        out = self.tmp / "scope-diff.json"
        result = subprocess.run(
            [sys.executable, SCRIPT, str(self.tmp / "nonexistent.md"), str(log), "-o", str(out)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(data["error"], "file_missing")
        self.assertFalse(data["primary_exists"])

    def test_empty_frontmatter_vs_empty_log_returns_polish(self) -> None:
        primary = textwrap.dedent("""\
            ---
            stage_2_actors: []
            stage_2_flows: []
            ---
            # Content
        """)
        log = textwrap.dedent("""\
            ## 2026-05-28T10:00 — Session: Create

            ### Sources
            - None
        """)
        data = _run(primary, log, self.tmp)
        self.assertEqual(data["scope"], "polish")

    def test_uses_last_flush_block_when_multiple_sessions(self) -> None:
        primary = textwrap.dedent("""\
            ---
            stage_2_actors: [User, System, NewActor]
            stage_2_flows: [Login]
            ---
            # Content
        """)
        log = textwrap.dedent("""\
            ## 2026-05-20T10:00 — Session: Create

            ### Discovery snapshot (Stage 2 flush)
            - **Actors:** User
            - **Flow inventory:**
            - **Login** — user authentication

            ## 2026-05-28T14:00 — Session: Update

            ### Discovery snapshot (Stage 2 flush)
            - **Actors:** User, System
            - **Flow inventory:**
            - **Login** — user authentication
        """)
        data = _run(primary, log, self.tmp)
        self.assertEqual(data["scope"], "semantic")
        self.assertTrue(data["actors_changed"])
        self.assertIn("NewActor", data["current_actors"])
        self.assertNotIn("NewActor", data["prior_actors"])


if __name__ == "__main__":
    unittest.main()
