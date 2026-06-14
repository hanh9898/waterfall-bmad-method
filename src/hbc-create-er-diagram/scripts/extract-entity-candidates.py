#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stage 2 pre-pass: extract entity, attribute, and relationship candidates
from source documents (PRD, Architecture, D-20, ORM models) for LLM
confirmation rather than free-reading raw sources.

CLI:
  extract-entity-candidates.py <source-path>... -o <output.json>

Each <source-path> may be a file or directory (walks *.md recursively).

Exit codes:
  0  candidates extracted (may be empty — see `warn` field)
  2  argument error or all paths unreadable
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

EXCLUDE_DIRS: frozenset[str] = frozenset(
    {"archive", "archived", "old", "notes", "scratch", "drafts", ".git", "node_modules", "__pycache__"}
)

STOP_WORDS: frozenset[str] = frozenset(
    {
        "the", "a", "an", "this", "that", "each", "every", "any", "all",
        "new", "main", "primary", "secondary", "following", "above", "below",
        "same", "other", "another", "such", "data", "database", "system",
        "application", "service", "api", "server", "client", "frontend",
        "backend", "module", "component", "function", "method", "class",
        "type", "interface", "schema", "diagram", "design", "document",
    }
)

EXPLICIT_ENTITY_RE = re.compile(
    r"(?:Entity|Table|Model)\s*[:：]\s*[`\"']?(\w+)[`\"']?",
    re.IGNORECASE,
)

DATA_OBJECT_RE = re.compile(
    r"\b(\w+)\s+(?:entity|table|model)\b",
    re.IGNORECASE,
)

D20_TABLE_HEADER_RE = re.compile(
    r"^#{2,3}\s+(?:Table)\s*[:：]?\s*[`\"']?(\w+)[`\"']?",
    re.IGNORECASE | re.MULTILINE,
)

ORM_MODEL_RE = re.compile(
    r"class\s+(\w+)\s*\(.*(?:Model|Base|Entity|Table)\b",
)

ATTRIBUTE_RE = re.compile(
    r"[-*]\s+[`\"']?(\w+)[`\"']?\s*[:：]\s*(\w+)",
)

RELATIONSHIP_RE = re.compile(
    r"(\w+)\s*(?:→|->|has many|has one|belongs to|references)\s*(\w+)",
    re.IGNORECASE,
)


def _walk_md(root: Path) -> list[Path]:
    out: list[Path] = []
    for f in root.rglob("*.md"):
        parts = {part.lower() for part in f.relative_to(root).parts[:-1]}
        if parts & {d.lower() for d in EXCLUDE_DIRS}:
            continue
        out.append(f)
    return sorted(out)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _is_valid(name: str) -> bool:
    return len(name) > 1 and name.lower() not in STOP_WORDS and not name.isupper() or len(name) <= 5


def _extract_from_text(text: str, source_file: str) -> tuple[list[dict], list[dict], list[dict]]:
    entities: dict[str, dict] = {}
    attributes: list[dict] = []
    relations: list[dict] = []

    for pattern, method in [
        (EXPLICIT_ENTITY_RE, "explicit_marker"),
        (DATA_OBJECT_RE, "data_object_ref"),
        (D20_TABLE_HEADER_RE, "d20_table_header"),
        (ORM_MODEL_RE, "orm_model"),
    ]:
        for m in pattern.finditer(text):
            name = m.group(1).strip()
            if not _is_valid(name):
                continue
            key = name.lower().replace("_", "")
            if key not in entities:
                entities[key] = {
                    "entity_name": name,
                    "method": method,
                    "source_file": source_file,
                    "line": text[:m.start()].count("\n") + 1,
                }

    for m in ATTRIBUTE_RE.finditer(text):
        attr_name = m.group(1).strip()
        attr_type = m.group(2).strip()
        if len(attr_name) > 1:
            attributes.append({
                "attribute_name": attr_name,
                "type_hint": attr_type,
                "source_file": source_file,
                "line": text[:m.start()].count("\n") + 1,
            })

    for m in RELATIONSHIP_RE.finditer(text):
        left = m.group(1).strip()
        right = m.group(2).strip()
        if _is_valid(left) and _is_valid(right):
            relations.append({
                "from_entity": left,
                "to_entity": right,
                "source_file": source_file,
                "line": text[:m.start()].count("\n") + 1,
            })

    return list(entities.values()), attributes, relations


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract entity candidates from source documents.")
    parser.add_argument("sources", nargs="+", help="Source file or directory paths.")
    parser.add_argument("-o", "--output", required=True, help="JSON output path.")
    args = parser.parse_args()

    all_entities: list[dict] = []
    all_attributes: list[dict] = []
    all_relations: list[dict] = []
    files_read: list[str] = []

    for src in args.sources:
        p = Path(src)
        if not p.exists():
            continue
        paths = _walk_md(p) if p.is_dir() else [p]
        for fp in paths:
            text = _read(fp)
            entities, attrs, rels = _extract_from_text(text, str(fp))
            all_entities.extend(entities)
            all_attributes.extend(attrs)
            all_relations.extend(rels)
            files_read.append(str(fp))

    seen: set[str] = set()
    deduped: list[dict] = []
    for e in all_entities:
        key = e["entity_name"].lower().replace("_", "")
        if key not in seen:
            seen.add(key)
            deduped.append(e)

    warn = None
    if not deduped and files_read:
        warn = "entity_extraction_empty"

    result = {
        "candidate_entities": deduped,
        "candidate_attributes": all_attributes,
        "candidate_relations": all_relations,
        "warn": warn,
        "files_read": files_read,
        "totals": {
            "entities": len(deduped),
            "attributes": len(all_attributes),
            "relations": len(all_relations),
            "files": len(files_read),
        },
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": args.output, "entities": len(deduped), "warn": warn}))
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
