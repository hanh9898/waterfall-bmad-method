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
        plan_dir = root / "_bmad-output" / "planning-artifacts"
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
        plan_dir = root / "_bmad-output" / "planning-artifacts"
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
        hbc = root / "_bmad-output" / "planning-artifacts"
        hbc.mkdir(parents=True)
        (root / "D-01-brief.md").write_text("# Brief\n", encoding="utf-8")
        (hbc / "D-01-brief.md").write_text("# Brief\n", encoding="utf-8")
        out = run_scan(tmp)
        d01_paths = [d["path"] for d in out["source_docs"] if "D-01" in d["path"]]
        assert len(d01_paths) <= 2


def test_d02_not_in_source_docs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plan = root / "_bmad-output" / "planning-artifacts"
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


def test_brownfield_suspected_existing_code_no_context():
    # Existing code marker (package.json) but no project-context.md → suspected
    # brownfield (the skill nudges to run Phase 0), NOT silently greenfield.
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "package.json").write_text('{"name":"x"}', encoding="utf-8")
        out = run_scan(tmp)
        assert out["brownfield"] is False
        assert out["brownfield_suspected"] is True
        assert "existing_system" not in out  # no AS-IS catalog without project-context


def test_brownfield_suspected_false_when_empty_or_context_present():
    with tempfile.TemporaryDirectory() as tmp:
        assert run_scan(tmp)["brownfield_suspected"] is False  # empty dir
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "package.json").write_text("{}", encoding="utf-8")
        (root / "project-context.md").write_text("# PC\n", encoding="utf-8")
        out = run_scan(tmp)
        assert out["brownfield"] is True
        assert out["brownfield_suspected"] is False  # already brownfield, not "suspected"


def test_greenfield_no_existing_system():
    # No project-context.md → not brownfield → no existing_system catalog.
    with tempfile.TemporaryDirectory() as tmp:
        out = run_scan(tmp)
        assert out["brownfield"] is False
        assert "existing_system" not in out


def test_brownfield_catalog_from_baselines():
    # project-context.md + baseline D-19/D-21 → catalog extracts entities + endpoints.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "project-context.md").write_text(
            "# Project Context\n## Technology Stack & Versions\nPython 3.12\n", encoding="utf-8")
        erd = root / "_bmad-output" / "shared" / "erd"
        erd.mkdir(parents=True)
        (erd / "D-19-baseline-erd.md").write_text(
            "# D-19\n\n```mermaid\nerDiagram\n  Customer { int id PK }\n  Order { int id PK }\n"
            "  Customer ||--o{ Order : places\n```\n", encoding="utf-8")
        api = root / "_bmad-output" / "shared" / "api"
        api.mkdir(parents=True)
        (api / "D-21-baseline-api.md").write_text(
            "# D-21\n\n## Endpoint List\n\n| # | Method | Endpoint | Description | REQ ID |\n"
            "|---|--------|----------|-------------|--------|\n"
            "| 1 | GET | /api/customers | list | REQ-001 |\n"
            "| 2 | POST | /api/orders | create | REQ-002 |\n", encoding="utf-8")
        out = run_scan(tmp)
        assert out["brownfield"] is True
        cat = out["existing_system"]
        assert "Customer" in cat["entities"] and "Order" in cat["entities"]
        assert "GET /api/customers" in cat["endpoints"]
        assert "POST /api/orders" in cat["endpoints"]
        assert "hint" not in cat


def test_brownfield_catalog_captures_relationship_only_entity():
    # det-01: an entity that appears ONLY in a relationship line (no {} block) must
    # still be captured, else the pick-list is incomplete.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "project-context.md").write_text("# PC\n## Technology Stack & Versions\nX\n", encoding="utf-8")
        erd = root / "_bmad-output" / "shared" / "erd"
        erd.mkdir(parents=True)
        (erd / "D-19-baseline.md").write_text(
            "# D-19\n\n```mermaid\nerDiagram\n  Customer { int id PK }\n"
            "  Customer ||--o{ Order : places\n```\n", encoding="utf-8")
        out = run_scan(tmp)
        ents = out["existing_system"]["entities"]
        assert "Customer" in ents and "Order" in ents  # Order has no {} block


def test_brownfield_hint_per_baseline_when_one_missing():
    # det-05: D-19 present but no D-21 → still hint (names the missing endpoints baseline).
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "project-context.md").write_text("# PC\n## Technology Stack & Versions\nX\n", encoding="utf-8")
        erd = root / "_bmad-output" / "shared" / "erd"
        erd.mkdir(parents=True)
        (erd / "D-19-baseline.md").write_text(
            "# D-19\n\n```mermaid\nerDiagram\n  Customer { int id PK }\n```\n", encoding="utf-8")
        out = run_scan(tmp)
        cat = out["existing_system"]
        assert cat["entities"] == ["Customer"]
        assert cat["endpoints"] == []
        assert "hint" in cat and "endpoint" in cat["hint"].lower()


def test_brownfield_thin_catalog_sets_hint():
    # Brownfield but no baseline D-19/D-21 → empty catalog + hint to run document-project.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "project-context.md").write_text(
            "# Project Context\n## Technology Stack & Versions\nPython\n", encoding="utf-8")
        out = run_scan(tmp)
        assert out["brownfield"] is True
        cat = out["existing_system"]
        assert cat["entities"] == [] and cat["endpoints"] == []
        assert "hint" in cat


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
