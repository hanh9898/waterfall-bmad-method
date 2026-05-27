#!/usr/bin/env python3
"""Tests for scan-sources.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "scan-sources.py")


def run_scan(project_root: str) -> dict:
    result = subprocess.run(
        [sys.executable, SCRIPT, "--project-root", project_root],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def test_empty_dir_returns_fresh():
    with tempfile.TemporaryDirectory() as tmp:
        out = run_scan(tmp)
        assert out["state"] == "fresh"
        assert out["existing_d02"] is None
        assert out["source_docs"] == []
        assert out["project_context"] is None


def test_complete_d02_returns_update():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan_dir = root / "_hbc_output" / "plan"
        plan_dir.mkdir(parents=True)
        d02 = plan_dir / "D-02-test-project.md"
        d02.write_text(
            "---\nlastStep: complete\nversion: \"1.0\"\nstatus: final\n---\n# D-02\n",
            encoding="utf-8",
        )
        out = run_scan(tmp)
        assert out["state"] == "update"
        assert out["existing_d02"] is not None
        assert out["existing_d02"]["lastStep"] == "complete"
        assert out["existing_d02"]["version"] == "1.0"


def test_partial_d02_returns_resume():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan_dir = root / "_hbc_output" / "plan"
        plan_dir.mkdir(parents=True)
        d02 = plan_dir / "D-02-test-project.md"
        d02.write_text(
            "---\nlastStep: Stage 2\nversion: \"0.1\"\n---\n# D-02\n",
            encoding="utf-8",
        )
        out = run_scan(tmp)
        assert out["state"] == "resume"
        assert out["existing_d02"]["lastStep"] == "Stage 2"


def test_project_context_discovery():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ctx = root / "docs" / "project-context.md"
        ctx.parent.mkdir(parents=True)
        ctx.write_text("# Project Context\n", encoding="utf-8")
        out = run_scan(tmp)
        assert out["project_context"] is not None
        assert "project-context.md" in out["project_context"]


def test_source_docs_discovery():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "D-01-brief.md").write_text("# Brief\n", encoding="utf-8")
        (root / "D-03-glossary.md").write_text("# Glossary\n", encoding="utf-8")
        out = run_scan(tmp)
        assert out["source_count"] >= 2
        paths = [d["path"] for d in out["source_docs"]]
        assert any("D-01" in p for p in paths)
        assert any("D-03" in p for p in paths)


def test_source_docs_dedup():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        hbc = root / "_hbc_output" / "plan"
        hbc.mkdir(parents=True)
        (root / "D-01-brief.md").write_text("# Brief\n", encoding="utf-8")
        (hbc / "D-01-brief.md").write_text("# Brief\n", encoding="utf-8")
        out = run_scan(tmp)
        d01_paths = [d["path"] for d in out["source_docs"] if "D-01" in d["path"]]
        assert len(d01_paths) <= 2


def test_d02_not_in_source_docs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = root / "_hbc_output" / "plan"
        plan.mkdir(parents=True)
        (plan / "D-02-test.md").write_text(
            "---\nlastStep: complete\n---\n# D-02\n", encoding="utf-8"
        )
        (plan / "D-01-brief.md").write_text("# Brief\n", encoding="utf-8")
        out = run_scan(tmp)
        source_paths = [d["path"] for d in out["source_docs"]]
        assert not any("D-02" in p for p in source_paths)


def test_no_frontmatter_d02():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "D-02-plain.md").write_text("# Just a title\n", encoding="utf-8")
        out = run_scan(tmp)
        assert out["state"] == "resume"
        assert out["existing_d02"]["lastStep"] == ""


def test_output_to_file():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = Path(tmp) / "result.json"
        result = subprocess.run(
            [sys.executable, SCRIPT, "--project-root", tmp, "-o", str(out_path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["state"] == "fresh"
