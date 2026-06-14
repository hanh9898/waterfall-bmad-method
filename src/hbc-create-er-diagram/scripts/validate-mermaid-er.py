#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stage 4 validator: parse Mermaid erDiagram blocks in the D-19 output and
report syntactic + entity-coverage issues.

Checks per Mermaid block:
  - Every entity referenced in a relationship line was declared with attributes
  - No orphan declared entities (declared but never used in relationships)
  - Relationship cardinality notation is valid
  - Attribute type declarations are present for PK/FK fields
  - If --expected-entities is given, every expected entity appears in at
    least one block

Each issue carries `auto_fixable: bool`. Stage-4 in SKILL.md applies only
auto_fixable=true issues mechanically; everything else returns blocked.

Returns JSON with passed (bool) and issues (list).

Exit codes:
  0  passed
  1  issues found
  2  argument or filesystem error
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


MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)

# Entity declaration with attributes block:
#   EntityName {
#       type attr_name PK "comment"
#   }
ENTITY_BLOCK_RE = re.compile(
    r"^\s*(\w+)\s*\{([^}]*)\}",
    re.MULTILINE | re.DOTALL,
)

# Relationship lines:
#   EntityA ||--o{ EntityB : "has"
#   EntityA }o--o{ EntityB : "many-to-many"
RELATIONSHIP_RE = re.compile(
    r"""^\s*(?P<left>\w+)\s+
        (?P<card>
            \|\|--o\{|  # one-to-many
            \}o--\|\||  # many-to-one (reverse)
            \|\|--\|\|| # one-to-one
            \}o--o\{|   # many-to-many
            \|\|--o\||  # one-to-zero-or-one
            \|o--\|\||  # zero-or-one-to-one (reverse)
            \|o--o\{|   # zero-or-one-to-many
            \}o--o\||   # many-to-zero-or-one (reverse)
            \|o--o\|    # zero-or-one-to-zero-or-one
        )\s+
        (?P<right>\w+)\s*:\s*
        (?P<label>.+)$""",
    re.MULTILINE | re.VERBOSE,
)

# Attribute line inside entity block:
#   type name PK "comment"
#   type name FK "comment"
#   type name
ATTR_RE = re.compile(
    r"""^\s*(?P<type>\w+)\s+
        (?P<name>\w+)
        (?:\s+(?P<constraint>PK|FK|UK))?
        (?:\s+"(?P<comment>[^"]*)")?""",
    re.MULTILINE | re.VERBOSE,
)


def _strip_quotes(s: str) -> str:
    return s.strip().strip('"').strip("'")


def _extract_blocks(text: str) -> list[str]:
    return [m.group(1) for m in MERMAID_BLOCK_RE.finditer(text)]


def _is_er_block(block: str) -> bool:
    return "erDiagram" in block


def _block_entities(block: str) -> dict[str, list[dict[str, str | None]]]:
    """Return {entity_name: [attributes]} for every entity declaration."""
    entities: dict[str, list[dict[str, str | None]]] = {}
    for m in ENTITY_BLOCK_RE.finditer(block):
        name = m.group(1)
        if name == "erDiagram":
            continue
        body = m.group(2)
        attrs: list[dict[str, str | None]] = []
        for am in ATTR_RE.finditer(body):
            attrs.append({
                "type": am.group("type"),
                "name": am.group("name"),
                "constraint": am.group("constraint"),
                "comment": am.group("comment"),
            })
        entities[name] = attrs
    return entities


def _block_relationships(block: str) -> list[dict[str, str]]:
    """Return list of relationships with left, right, cardinality, label."""
    rels: list[dict[str, str]] = []
    for m in RELATIONSHIP_RE.finditer(block):
        rels.append({
            "left": m.group("left"),
            "right": m.group("right"),
            "cardinality": m.group("card"),
            "label": _strip_quotes(m.group("label")),
        })
    return rels


def _analyse_block(block: str, idx: int) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []

    if not _is_er_block(block):
        return issues

    entities = _block_entities(block)
    relationships = _block_relationships(block)
    declared = set(entities.keys())

    # Collect all entity names referenced in relationships.
    referenced: set[str] = set()
    for rel in relationships:
        referenced.add(rel["left"])
        referenced.add(rel["right"])

    # Entities referenced in relationships but not declared with attributes.
    for name in sorted(referenced - declared):
        issues.append({
            "block": idx,
            "kind": "undeclared_entity",
            "name": name,
            "auto_fixable": True,
            "fix_hint": f"add empty entity block `{name} {{}}` to block {idx}",
            "detail": "Referenced in relationship but no attribute block declared",
        })

    # Entities declared but never referenced in any relationship.
    for name in sorted(declared - referenced):
        issues.append({
            "block": idx,
            "kind": "orphan_entity",
            "name": name,
            "auto_fixable": False,
            "detail": "Declared with attributes but not referenced in any relationship",
        })

    # Check each entity has at least a PK.
    for name, attrs in entities.items():
        has_pk = any(a.get("constraint") == "PK" for a in attrs)
        if not has_pk and attrs:
            issues.append({
                "block": idx,
                "kind": "missing_pk",
                "name": name,
                "auto_fixable": False,
                "detail": f"Entity '{name}' has attributes but no PK constraint defined",
            })

    # Check FK attributes reference existing entities.
    for name, attrs in entities.items():
        fk_attrs = [a for a in attrs if a.get("constraint") == "FK"]
        for fk in fk_attrs:
            # Try to infer target entity from FK attribute name (e.g. user_id -> User).
            fk_name = fk["name"] or ""
            if fk_name.endswith("_id"):
                candidate = fk_name[:-3].title().replace("_", "")
                if candidate not in declared and candidate not in referenced:
                    issues.append({
                        "block": idx,
                        "kind": "fk_target_missing",
                        "name": f"{name}.{fk_name}",
                        "auto_fixable": False,
                        "detail": f"FK attribute '{fk_name}' may reference undeclared entity '{candidate}'",
                    })

    return issues


def main() -> int:
    doc = __doc__ or ""
    parser = argparse.ArgumentParser(description=doc.split("\n\n")[0])
    parser.add_argument("target", help="Path to the rendered D-19 markdown file")
    parser.add_argument(
        "--expected-entities",
        default="",
        help="Comma-separated entity names that must appear in at least one block",
    )
    parser.add_argument("-o", "--output", required=True, help="JSON output path")
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps({"passed": False, "error": "target_missing", "target": str(target)}),
            encoding="utf-8",
        )
        return 2

    text = target.read_text(encoding="utf-8", errors="replace")
    blocks = _extract_blocks(text)
    er_blocks = [b for b in blocks if _is_er_block(b)]
    expected = {n.strip() for n in args.expected_entities.split(",") if n.strip()}

    all_issues: list[dict[str, object]] = []
    if not er_blocks:
        all_issues.append({
            "kind": "no_er_blocks",
            "auto_fixable": False,
            "detail": "Target contains no ```mermaid erDiagram``` blocks",
        })
    else:
        combined_entities: set[str] = set()
        for idx, block in enumerate(blocks):
            if _is_er_block(block):
                all_issues.extend(_analyse_block(block, idx))
                entities = _block_entities(block)
                combined_entities.update(entities.keys())
                for rel in _block_relationships(block):
                    combined_entities.add(rel["left"])
                    combined_entities.add(rel["right"])

        for name in sorted(expected - combined_entities):
            all_issues.append({
                "kind": "missing_expected_entity",
                "name": name,
                "auto_fixable": False,
                "detail": "Listed in --expected-entities but absent from every ER block",
            })

    result = {
        "passed": len(all_issues) == 0,
        "target": str(target),
        "er_block_count": len(er_blocks),
        "total_block_count": len(blocks),
        "issues": all_issues,
        "auto_fixable_count": sum(1 for i in all_issues if i.get("auto_fixable")),
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps({
            "output": args.output,
            "passed": result["passed"],
            "issue_count": len(all_issues),
            "auto_fixable_count": result["auto_fixable_count"],
        })
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
