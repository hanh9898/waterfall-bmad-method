#!/usr/bin/env python3
"""Tests for scan-glossary-sources.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "scan-glossary-sources.py")


def run_script(project_root: str) -> dict:
    cmd = [sys.executable, SCRIPT, "--project-root", project_root]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_fresh_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_script(tmpdir)
        assert result["state"] == "fresh"
        assert result["existing_d03"] is None
        assert result["source_count"] == 0
        assert result["candidate_count"] == 0


def test_resume_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        d03 = Path(tmpdir) / "D-03-test.md"
        d03.write_text("---\nlastStep: discovery\nversion: '0.1'\n---\n# Glossary\n", encoding="utf-8")
        result = run_script(tmpdir)
        assert result["state"] == "resume"
        assert result["existing_d03"]["lastStep"] == "discovery"


def test_update_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        d03 = Path(tmpdir) / "D-03-test.md"
        d03.write_text("---\nlastStep: complete\nversion: '1.0'\n---\n# Glossary\n", encoding="utf-8")
        result = run_script(tmpdir)
        assert result["state"] == "update"
        assert result["existing_d03"]["lastStep"] == "complete"


def test_discovers_source_docs():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "D-02-requirements.md").write_text("# Requirements\n", encoding="utf-8")
        (Path(tmpdir) / "D-01-brief.md").write_text("# Brief\n", encoding="utf-8")
        result = run_script(tmpdir)
        assert result["source_count"] == 2
        names = {d["name"] for d in result["source_docs"]}
        assert "D-02-requirements.md" in names
        assert "D-01-brief.md" in names


def test_discovers_project_context():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "project-context.md").write_text("# Context\n**Domain Term**\n", encoding="utf-8")
        result = run_script(tmpdir)
        assert result["source_count"] == 1
        assert result["source_docs"][0]["name"] == "project-context.md"
        assert result["candidate_count"] >= 1


def test_extract_jp_quotes():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "D-02-test.md").write_text("「オーダー」を処理する\n", encoding="utf-8")
        result = run_script(tmpdir)
        terms = [c["term"] for c in result["raw_candidates"]]
        assert "オーダー" in terms
        methods = {c["method"] for c in result["raw_candidates"] if c["term"] == "オーダー"}
        assert "jp_quote" in methods


def test_extract_md_bold():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "D-02-test.md").write_text("Use **Order Status** for tracking\n", encoding="utf-8")
        result = run_script(tmpdir)
        terms = [c["term"] for c in result["raw_candidates"]]
        assert "Order Status" in terms
        methods = {c["method"] for c in result["raw_candidates"] if c["term"] == "Order Status"}
        assert "md_bold" in methods


def test_extract_md_italic():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "D-02-test.md").write_text("The _validation rule_ applies here\n", encoding="utf-8")
        result = run_script(tmpdir)
        terms = [c["term"] for c in result["raw_candidates"]]
        assert "validation rule" in terms


def test_extract_abbreviations():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "D-02-test.md").write_text("OMS and SKU are key terms\n", encoding="utf-8")
        result = run_script(tmpdir)
        terms = [c["term"] for c in result["raw_candidates"]]
        assert "OMS" in terms
        assert "SKU" in terms
        methods = {c["method"] for c in result["raw_candidates"] if c["term"] == "OMS"}
        assert "abbreviation" in methods


def test_extract_vi_quotes():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "D-02-test.md").write_text("“Hệ thống quản lý” là thuật ngữ chính\n", encoding="utf-8")
        result = run_script(tmpdir)
        terms = [c["term"] for c in result["raw_candidates"]]
        assert "Hệ thống quản lý" in terms


def test_deduplicates_candidates():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "D-02-test.md").write_text("**Order** and **Order** again\n", encoding="utf-8")
        result = run_script(tmpdir)
        terms = [c["term"] for c in result["raw_candidates"]]
        assert terms.count("Order") == 1


def test_output_to_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "result.json"
        cmd = [sys.executable, SCRIPT, "--project-root", tmpdir, "-o", str(out_path)]
        subprocess.run(cmd, capture_output=True, text=True)
        assert out_path.exists()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert "state" in data


if __name__ == "__main__":
    tests = [
        test_fresh_project,
        test_resume_state,
        test_update_state,
        test_discovers_source_docs,
        test_discovers_project_context,
        test_extract_jp_quotes,
        test_extract_md_bold,
        test_extract_md_italic,
        test_extract_abbreviations,
        test_extract_vi_quotes,
        test_deduplicates_candidates,
        test_output_to_file,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
