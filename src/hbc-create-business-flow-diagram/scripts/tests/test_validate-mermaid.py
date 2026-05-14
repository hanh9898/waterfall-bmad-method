#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Tests for validate-mermaid.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "validate-mermaid.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def make_md(tmpdir: Path, body: str) -> Path:
    target = tmpdir / "doc.md"
    target.write_text(body, encoding="utf-8")
    return target


class ValidateMermaidTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "out.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _result(self) -> dict[str, object]:
        return json.loads(self.out.read_text(encoding="utf-8"))

    def test_clean_block_passes(self) -> None:
        body = """# Doc

```mermaid
sequenceDiagram
    actor User as User
    participant System as System
    User->>System: Action
    System-->>User: Result
```
"""
        target = make_md(self.root, body)
        proc = run_script(str(target), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        result = self._result()
        self.assertTrue(result["passed"])
        self.assertEqual(result["block_count"], 1)

    def test_quoted_alias_declarations_parsed(self) -> None:
        # Two valid Mermaid quoted forms — both must parse.
        #   (a) `participant OS as "Order Service"` — short id, quoted display
        #   (b) `participant "Cust Svc"` — id with spaces, no display
        body = """```mermaid
sequenceDiagram
    participant OS as "Order Service"
    participant "Cust Svc"
    OS->>"Cust Svc": Forward
    "Cust Svc"-->>OS: Ack
```
"""
        target = make_md(self.root, body)
        proc = run_script(str(target), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        result = self._result()
        self.assertTrue(result["passed"], f"issues: {result.get('issues')}")

    def test_note_over_participant_not_orphan(self) -> None:
        body = """```mermaid
sequenceDiagram
    participant A as A
    participant B as B
    participant Auditor as Auditor
    A->>B: Request
    B-->>A: Response
    Note over Auditor: Logs the exchange
```
"""
        target = make_md(self.root, body)
        proc = run_script(str(target), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0, f"stderr: {proc.stderr}")
        result = self._result()
        # Auditor declared but only referenced in Note — should NOT be orphan
        orphans = [i for i in result["issues"] if i.get("kind") == "orphan_declaration"]
        self.assertEqual(orphans, [])

    def test_activation_prefix_recognised(self) -> None:
        body = """```mermaid
sequenceDiagram
    participant Caller as Caller
    participant Service as Service
    Caller->>+Service: Begin
    Service-->>-Caller: Done
    activate Service
    deactivate Service
```
"""
        target = make_md(self.root, body)
        proc = run_script(str(target), "-o", str(self.out))
        self.assertEqual(proc.returncode, 0)
        result = self._result()
        self.assertTrue(result["passed"], f"issues: {result.get('issues')}")

    def test_undeclared_participant_flagged_auto_fixable(self) -> None:
        body = """```mermaid
sequenceDiagram
    participant User as User
    User->>Ghost: Send
    Ghost-->>User: Reply
```
"""
        target = make_md(self.root, body)
        proc = run_script(str(target), "-o", str(self.out))
        self.assertEqual(proc.returncode, 1, "should fail when participant undeclared")
        result = self._result()
        issues = [i for i in result["issues"] if i.get("kind") == "undeclared_participant"]
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["name"], "Ghost")
        self.assertTrue(issues[0]["auto_fixable"])
        self.assertEqual(result["auto_fixable_count"], 1)

    def test_expected_actor_missing_flagged_not_auto_fixable(self) -> None:
        body = """```mermaid
sequenceDiagram
    participant User as User
    participant System as System
    User->>System: Request
    System-->>User: Response
```
"""
        target = make_md(self.root, body)
        proc = run_script(
            str(target),
            "--expected-actors", "User,System,Admin",
            "-o", str(self.out),
        )
        self.assertEqual(proc.returncode, 1)
        result = self._result()
        missing = [i for i in result["issues"] if i.get("kind") == "missing_expected_actor"]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["name"], "Admin")
        self.assertFalse(missing[0]["auto_fixable"])

    def test_no_mermaid_blocks_flagged(self) -> None:
        target = make_md(self.root, "# Doc with no diagrams\n")
        proc = run_script(str(target), "-o", str(self.out))
        self.assertEqual(proc.returncode, 1)
        result = self._result()
        self.assertEqual(len(result["issues"]), 1)
        self.assertEqual(result["issues"][0]["kind"], "no_mermaid_blocks")


if __name__ == "__main__":
    unittest.main()
