#!/usr/bin/env python3
"""Tests for check-entity-coverage.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-entity-coverage.py")


def run_script(prd_paths: list[str], d19_path: str, output_path: str) -> dict:
    cmd = [sys.executable, SCRIPT, "--d19", d19_path, "-o", output_path]
    for p in prd_paths:
        cmd.extend(["--prd", p])
    subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(Path(output_path).read_text(encoding="utf-8"))


def test_perfect_coverage():
    with tempfile.TemporaryDirectory() as tmpdir:
        prd = Path(tmpdir) / "prd.md"
        prd.write_text("Entity: Users\nEntity: Orders\n", encoding="utf-8")
        d19 = Path(tmpdir) / "d19.md"
        d19.write_text(
            "```mermaid\nerDiagram\n  Users {\n    int id PK\n  }\n  Orders {\n    int id PK\n  }\n  Users ||--o{ Orders : has\n```\n",
            encoding="utf-8",
        )
        out = str(Path(tmpdir) / "out.json")
        data = run_script([str(prd)], str(d19), out)
        assert data["passed"] is True
        assert len(data["uncovered"]) == 0
        assert len(data["phantom"]) == 0


def test_uncovered_entity():
    with tempfile.TemporaryDirectory() as tmpdir:
        prd = Path(tmpdir) / "prd.md"
        prd.write_text("Entity: Users\nEntity: Orders\nEntity: Payments\n", encoding="utf-8")
        d19 = Path(tmpdir) / "d19.md"
        d19.write_text(
            "```mermaid\nerDiagram\n  Users {\n    int id PK\n  }\n  Orders {\n    int id PK\n  }\n  Users ||--o{ Orders : has\n```\n",
            encoding="utf-8",
        )
        out = str(Path(tmpdir) / "out.json")
        data = run_script([str(prd)], str(d19), out)
        assert data["passed"] is False
        assert "Payments" in data["uncovered"]


def test_phantom_entity():
    with tempfile.TemporaryDirectory() as tmpdir:
        prd = Path(tmpdir) / "prd.md"
        prd.write_text("Entity: Users\n", encoding="utf-8")
        d19 = Path(tmpdir) / "d19.md"
        d19.write_text(
            "```mermaid\nerDiagram\n  Users {\n    int id PK\n  }\n  Ghosts {\n    int id PK\n  }\n  Users ||--o{ Ghosts : haunts\n```\n",
            encoding="utf-8",
        )
        out = str(Path(tmpdir) / "out.json")
        data = run_script([str(prd)], str(d19), out)
        assert data["passed"] is False
        assert "Ghosts" in data["phantom"]


def test_fuzzy_match_plurals():
    with tempfile.TemporaryDirectory() as tmpdir:
        prd = Path(tmpdir) / "prd.md"
        prd.write_text("Entity: User\n", encoding="utf-8")
        d19 = Path(tmpdir) / "d19.md"
        d19.write_text(
            "```mermaid\nerDiagram\n  Users {\n    int id PK\n  }\n```\n",
            encoding="utf-8",
        )
        out = str(Path(tmpdir) / "out.json")
        data = run_script([str(prd)], str(d19), out)
        assert data["passed"] is True
        assert data["totals"]["covered"] == 1


def test_empty_prd_warns():
    with tempfile.TemporaryDirectory() as tmpdir:
        prd = Path(tmpdir) / "prd.md"
        prd.write_text("This PRD contains only narrative text.\n", encoding="utf-8")
        d19 = Path(tmpdir) / "d19.md"
        d19.write_text(
            "```mermaid\nerDiagram\n  Users {\n    int id PK\n  }\n```\n",
            encoding="utf-8",
        )
        out = str(Path(tmpdir) / "out.json")
        data = run_script([str(prd)], str(d19), out)
        assert data["warn"] == "prd_entity_extraction_empty"


def test_explicit_markers():
    with tempfile.TemporaryDirectory() as tmpdir:
        prd = Path(tmpdir) / "prd.md"
        prd.write_text("Table: Orders\nEntity: Shipments\n", encoding="utf-8")
        d19 = Path(tmpdir) / "d19.md"
        d19.write_text(
            "```mermaid\nerDiagram\n  Orders {\n    int id PK\n  }\n  Shipments {\n    int id PK\n  }\n  Orders ||--o{ Shipments : ships\n```\n",
            encoding="utf-8",
        )
        out = str(Path(tmpdir) / "out.json")
        data = run_script([str(prd)], str(d19), out)
        assert data["passed"] is True
        assert data["totals"]["prd_entities"] == 2


def test_missing_d19():
    with tempfile.TemporaryDirectory() as tmpdir:
        prd = Path(tmpdir) / "prd.md"
        prd.write_text("Entity: Users\n", encoding="utf-8")
        out = str(Path(tmpdir) / "out.json")
        data = run_script([str(prd)], str(Path(tmpdir) / "nonexist.md"), out)
        assert data["passed"] is False
        assert data["error"] == "d19_missing"


def test_relationship_only_entities_captured():
    # Bug C3: entities that appear only on a `}|--|{` relationship line (no `{}`
    # attribute block) were invisible because that cardinality token was not in the
    # enumerated list, so PRD entities were falsely reported uncovered.
    with tempfile.TemporaryDirectory() as tmpdir:
        prd = Path(tmpdir) / "prd.md"
        prd.write_text("Entity: Invoice\nEntity: Lineitem\n", encoding="utf-8")
        d19 = Path(tmpdir) / "d19.md"
        d19.write_text(
            "```mermaid\nerDiagram\n  INVOICE }|--|{ LINEITEM : contains\n```\n",
            encoding="utf-8",
        )
        out = str(Path(tmpdir) / "out.json")
        data = run_script([str(prd)], str(d19), out)
        assert "Invoice" not in data["uncovered"]
        assert "Lineitem" not in data["uncovered"]


if __name__ == "__main__":
    tests = [
        test_perfect_coverage,
        test_uncovered_entity,
        test_phantom_entity,
        test_fuzzy_match_plurals,
        test_empty_prd_warns,
        test_explicit_markers,
        test_missing_d19,
        test_relationship_only_entities_captured,
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
