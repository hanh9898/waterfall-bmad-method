#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stage 4 validator: extract data entity references from PRD and the D-19
output, return covered / uncovered / phantom sets.

  covered    = entities referenced in both PRD and D-19
  uncovered  = entities in PRD but not referenced in any D-19 ER diagram
  phantom    = entities in D-19 but not mentioned in PRD

Entity extraction from PRD uses heuristics:
  - Explicit entity markers: "Entity: X", "Table: X", "テーブル: X"
  - Data model sections with entity-like nouns
  - FR identifiers mentioning data objects

When `--prd` points to a directory the script walks markdown recursively,
skipping common stale folders.

CLI shape matches the sibling validator scripts:
  --d19 <path>       D-19 markdown file (the validation target)
  --prd <path>       PRD source — file or directory. Repeatable.
  -o / --output      JSON sink

Exit codes:
  0  no uncovered, no phantom
  1  coverage gaps found
  2  PRD or D-19 file unreadable / argument error
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# Mermaid ER entity names (word characters only, inside erDiagram blocks).
MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
ENTITY_NAME_RE = re.compile(r"^\s*(\w+)\s*\{", re.MULTILINE)
RELATIONSHIP_ENTITY_RE = re.compile(
    r"""^\s*(\w+)\s+
        (?:\|\|--o\{|\}o--\|\||\|\|--\|\||\}o--o\{|\|\|--o\||\|o--\|\||\|o--o\{|\}o--o\||\|o--o\|)\s+
        (\w+)\s*:""",
    re.MULTILINE | re.VERBOSE,
)

# PRD entity extraction patterns.
# Explicit markers: "Entity: Users", "Table: orders", "テーブル: 注文"
EXPLICIT_ENTITY_RE = re.compile(
    r"(?:Entity|Table|テーブル|エンティティ|Model)\s*[:：]\s*[`\"']?(\w+)[`\"']?",
    re.IGNORECASE,
)

# Data object references in requirement text: "the User entity", "Orders table"
DATA_OBJECT_RE = re.compile(
    r"\b(\w+)\s+(?:entity|table|model|テーブル|エンティティ|モデル)\b",
    re.IGNORECASE,
)

# Directories never walked for entity extraction.
EXCLUDE_DIRS: frozenset[str] = frozenset(
    {"archive", "archived", "old", "notes", "scratch", "drafts", ".git", "node_modules", "__pycache__"}
)

# Common words that are not entities.
STOP_WORDS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "this", "that", "each", "every", "any", "all",
        "new", "main", "primary", "secondary", "following", "above", "below",
        "same", "other", "another", "such", "data", "database", "system",
        "application", "service", "API", "server", "client", "frontend",
        "backend", "module", "component", "function", "method", "class",
        "type", "interface", "schema", "diagram", "design", "document",
    }
)


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _walk_md(root: Path) -> list[Path]:
    out: list[Path] = []
    for f in root.rglob("*.md"):
        parts = {part.lower() for part in f.relative_to(root).parts[:-1]}
        if parts & {d.lower() for d in EXCLUDE_DIRS}:
            continue
        out.append(f)
    return sorted(out)


def _extract_d19_entities(text: str) -> set[str]:
    """Extract entity names from D-19 Mermaid erDiagram blocks."""
    entities: set[str] = set()
    for block_match in MERMAID_BLOCK_RE.finditer(text):
        block = block_match.group(1)
        if "erDiagram" not in block:
            continue
        for m in ENTITY_NAME_RE.finditer(block):
            name = m.group(1)
            if name != "erDiagram":
                entities.add(name)
        for m in RELATIONSHIP_ENTITY_RE.finditer(block):
            entities.add(m.group(1))
            entities.add(m.group(2))
    return entities


def _extract_prd_entities(text: str) -> set[str]:
    """Extract data entity references from PRD text using heuristics."""
    entities: set[str] = set()
    for m in EXPLICIT_ENTITY_RE.finditer(text):
        name = m.group(1).strip()
        if name.lower() not in STOP_WORDS and len(name) > 1:
            entities.add(name)
    for m in DATA_OBJECT_RE.finditer(text):
        name = m.group(1).strip()
        if name.lower() not in STOP_WORDS and len(name) > 1:
            entities.add(name)
    return entities


def _normalize(name: str) -> str:
    """Normalize entity name for comparison: lowercase, strip trailing s."""
    n = name.lower().replace("_", "").replace("-", "")
    if n.endswith("s") and len(n) > 3:
        n = n[:-1]
    return n


def _fuzzy_match(prd_entities: set[str], d19_entities: set[str]) -> tuple[set[str], set[str], set[str]]:
    """Match PRD entities to D-19 entities with normalization."""
    prd_norm = {_normalize(e): e for e in prd_entities}
    d19_norm = {_normalize(e): e for e in d19_entities}

    covered_prd: set[str] = set()
    covered_d19: set[str] = set()

    for pn, pe in prd_norm.items():
        if pn in d19_norm:
            covered_prd.add(pe)
            covered_d19.add(d19_norm[pn])

    uncovered = prd_entities - covered_prd
    phantom = d19_entities - covered_d19

    return covered_prd, uncovered, phantom


def _gather_prd_entities(prd_paths: list[Path]) -> tuple[set[str], list[str]]:
    """Return (entity set, list of files actually read)."""
    entities: set[str] = set()
    read: list[str] = []
    for p in prd_paths:
        if not p.exists():
            continue
        if p.is_dir():
            for f in _walk_md(p):
                entities |= _extract_prd_entities(_read_text(f))
                read.append(str(f))
        else:
            entities |= _extract_prd_entities(_read_text(p))
            read.append(str(p))
    return entities, read


def main() -> int:
    doc = __doc__ or ""
    parser = argparse.ArgumentParser(description=doc.split("\n\n")[0])
    parser.add_argument(
        "--prd",
        required=True,
        action="append",
        help="PRD file or directory. Repeat for sharded PRDs or multiple sources.",
    )
    parser.add_argument(
        "--d19",
        required=True,
        help="Path to D-19 markdown file (the validation target).",
    )
    parser.add_argument("-o", "--output", required=True, help="JSON output path")
    args = parser.parse_args()

    prd_paths = [Path(p) for p in args.prd]
    d19 = Path(args.d19)

    if not d19.exists():
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps({"passed": False, "error": "d19_missing", "path": str(d19)}),
            encoding="utf-8",
        )
        return 2

    missing_prd = [p for p in prd_paths if not p.exists()]
    if missing_prd:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps(
                {"passed": False, "error": "prd_missing", "paths": [str(p) for p in missing_prd]}
            ),
            encoding="utf-8",
        )
        return 2

    prd_entities, prd_files_read = _gather_prd_entities(prd_paths)
    d19_entities = _extract_d19_entities(_read_text(d19))

    covered, uncovered, phantom = _fuzzy_match(prd_entities, d19_entities)

    result = {
        "passed": not uncovered and not phantom,
        "prd_paths": [str(p) for p in prd_paths],
        "prd_files_read": prd_files_read,
        "d19_path": str(d19),
        "covered": sorted(covered),
        "uncovered": sorted(uncovered),
        "phantom": sorted(phantom),
        "totals": {
            "prd_entities": len(prd_entities),
            "d19_entities": len(d19_entities),
            "covered": len(covered),
            "uncovered": len(uncovered),
            "phantom": len(phantom),
        },
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps({
            "output": args.output,
            "passed": result["passed"],
            "covered": len(covered),
            "uncovered": len(uncovered),
            "phantom": len(phantom),
        })
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
