#!/usr/bin/env python3
"""Tests for scan-coding-standards.py (D-12 discovery + framework detect + brownfield ingest)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "scan-coding-standards.py")


def run(args: list[str]) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


def test_fresh_when_no_d12():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        out = tmp / "out"
        out.mkdir()
        result, rc = run(["--project-root", str(tmp), "--output-dir", str(out)])
        assert result["state"] == "fresh"
        assert result["existing_d12"] is None
        assert rc == 0


def test_update_when_complete_d12_exists():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        out = tmp / "out"
        out.mkdir()
        (out / "D-12-demo.md").write_text(
            "---\nlastStep: complete\n---\n# D-12\n", encoding="utf-8"
        )
        result, rc = run(["--project-root", str(tmp), "--output-dir", str(out)])
        assert result["state"] == "update"
        assert result["existing_d12"]["file"] == "D-12-demo.md"


def test_resume_when_partial_d12():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        out = tmp / "out"
        out.mkdir()
        (out / "D-12-demo.md").write_text(
            "---\nlastStep: generation\n---\n# D-12\n", encoding="utf-8"
        )
        result, rc = run(["--project-root", str(tmp), "--output-dir", str(out)])
        assert result["state"] == "resume"


def test_framework_detected_from_project_context():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        out = tmp / "out"
        out.mkdir()
        (tmp / "project-context.md").write_text(
            "This project uses Odoo with _inherit and ir.model patterns.",
            encoding="utf-8",
        )
        result, rc = run(["--project-root", str(tmp), "--output-dir", str(out)])
        assert result["framework"] == "odoo"


def test_brownfield_knowledge_empty_when_dir_absent():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        out = tmp / "out"
        out.mkdir()
        result, rc = run([
            "--project-root", str(tmp), "--output-dir", str(out),
            "--project-knowledge", str(tmp / "no-docs"),
        ])
        assert result["project_knowledge_docs"] == []
        assert result["project_knowledge_count"] == 0


def test_brownfield_docs_ingested_when_present():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        out = tmp / "out"
        out.mkdir()
        docs = tmp / "docs"
        docs.mkdir()
        (docs / "index.md").write_text("# Index", encoding="utf-8")
        (docs / "conventions.md").write_text("# Conventions", encoding="utf-8")
        result, rc = run([
            "--project-root", str(tmp), "--output-dir", str(out),
            "--project-knowledge", str(docs),
        ])
        names = {dc["name"] for dc in result["project_knowledge_docs"]}
        assert "index.md" in names and "conventions.md" in names


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
