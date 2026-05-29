#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stage 4 validator: parse Mermaid blocks in the D-06 output and report
syntactic + actor-coverage issues.

Checks per Mermaid block:
  - Every participant/actor referenced in an arrow line was declared
  - No orphan declared participants/actors (declared but never used, unless
    referenced by a Note over / Note left of / Note right of line, which
    count as use)
  - Activation prefixes (`+A`, `-A`, `activate A`, `deactivate A`) are
    recognised
  - Quoted-alias declarations (`participant "Order Service" as OS`) parse
    correctly
  - If --expected-actors is given, every expected actor appears in at
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
from pathlib import Path


MERMAID_BLOCK_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)

# Declaration forms supported:
#   participant Alias
#   participant Alias as Display Label
#   participant "Quoted Alias" as Display
#   participant "Quoted Alias"
#   actor variants of all the above
DECL_RE = re.compile(
    r"""^\s*(participant|actor)\s+
        (?:"(?P<quoted>[^"]+)"|(?P<bare>\w+))
        (?:\s+as\s+(?P<display>.+))?\s*$""",
    re.MULTILINE | re.VERBOSE,
)

# Arrow forms in sequenceDiagram (source on left, target on right). Each
# side may carry an activation prefix (`+`, `-`).
ARROW_RE = re.compile(
    r"""^\s*
        \+?(?P<src>"[^"]+"|\w+)
        \s*(?:->>?|-->>?|--?\)|--?x|--?X)\s*
        [+-]?(?P<dst>"[^"]+"|\w+)
        \s*:""",
    re.MULTILINE | re.VERBOSE,
)

# `Note over A,B: msg` / `Note left of A: msg` / `Note right of A: msg`
NOTE_RE = re.compile(
    r"""^\s*Note\s+(?:over|left\s+of|right\s+of)\s+
        (?P<targets>[\w\",\s]+?)\s*:""",
    re.MULTILINE | re.IGNORECASE | re.VERBOSE,
)

# `activate A` / `deactivate A`
ACTIVATION_RE = re.compile(
    r"""^\s*(?:activate|deactivate)\s+
        (?P<name>"[^"]+"|\w+)\s*$""",
    re.MULTILINE | re.VERBOSE,
)


def _strip_quotes(name: str) -> str:
    return name[1:-1] if name.startswith('"') and name.endswith('"') else name


def _extract_blocks(text: str) -> list[str]:
    return [m.group(1) for m in MERMAID_BLOCK_RE.finditer(text)]


def _block_declarations(block: str) -> dict[str, dict[str, str | None]]:
    """Return {alias: {display, kind}} for every participant/actor decl."""
    decls: dict[str, dict[str, str | None]] = {}
    for m in DECL_RE.finditer(block):
        kind = m.group(1)
        alias = m.group("quoted") or m.group("bare")
        display = m.group("display").strip() if m.group("display") else None
        decls[alias] = {"display": display, "kind": kind}
    return decls


def _block_uses(block: str) -> tuple[set[str], dict[str, int]]:
    """Return (set of used names, arrow_count per name).

    Used = appears in an arrow source/target, an activation/deactivation,
    or a Note over/left of/right of target list.
    """
    used: set[str] = set()
    arrow_count: dict[str, int] = {}

    for m in ARROW_RE.finditer(block):
        for name in (_strip_quotes(m.group("src")), _strip_quotes(m.group("dst"))):
            used.add(name)
            arrow_count[name] = arrow_count.get(name, 0) + 1

    for m in ACTIVATION_RE.finditer(block):
        used.add(_strip_quotes(m.group("name")))

    for m in NOTE_RE.finditer(block):
        for raw in m.group("targets").split(","):
            cleaned = _strip_quotes(raw.strip())
            if cleaned:
                used.add(cleaned)

    return used, arrow_count


DIAGRAM_TYPE_RE = re.compile(r"^\s*(sequenceDiagram|flowchart|graph|stateDiagram(?:-v2)?)\b", re.MULTILINE)


def _detect_diagram_type(block: str) -> str | None:
    m = DIAGRAM_TYPE_RE.search(block)
    return m.group(1) if m else None


def _analyse_block(block: str, idx: int) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []

    diagram_type = _detect_diagram_type(block)
    if diagram_type and diagram_type != "sequenceDiagram":
        issues.append(
            {
                "block": idx,
                "kind": "diagram_type_unsupported",
                "diagram_type": diagram_type,
                "auto_fixable": False,
                "detail": f"Structural checks only cover sequenceDiagram; {diagram_type} block validated by LLM judgment only",
            }
        )
        return issues

    decls = _block_declarations(block)
    declared = set(decls.keys())
    used, arrow_count = _block_uses(block)

    for name in sorted(used - declared):
        # Auto-fixable when the name appears in arrow lines (any count) and
        # no declared participant carries a conflicting display label.
        ac = arrow_count.get(name, 0)
        conflict = any(
            (info["display"] or "").strip() == name for info in decls.values()
        )
        auto_fixable = ac >= 1 and not conflict
        issues.append(
            {
                "block": idx,
                "kind": "undeclared_participant",
                "name": name,
                "arrow_count": ac,
                "auto_fixable": auto_fixable,
                "fix_hint": f'add `participant {name}` at top of block {idx}' if auto_fixable else None,
                "detail": "Referenced but never declared with participant/actor",
            }
        )

    for name in sorted(declared - used):
        issues.append(
            {
                "block": idx,
                "kind": "orphan_declaration",
                "name": name,
                "auto_fixable": False,
                "detail": "Declared but never used in arrows, activations, or Notes",
            }
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("target", help="Path to the rendered D-06 markdown file")
    parser.add_argument(
        "--expected-actors",
        default="",
        help="Comma-separated names that must appear in at least one block",
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
    expected = {n.strip() for n in args.expected_actors.split(",") if n.strip()}

    all_issues: list[dict[str, object]] = []
    if not blocks:
        all_issues.append(
            {
                "kind": "no_mermaid_blocks",
                "auto_fixable": False,
                "detail": "Target contains no ```mermaid``` blocks",
            }
        )
    else:
        combined_names: set[str] = set()
        for idx, block in enumerate(blocks):
            all_issues.extend(_analyse_block(block, idx))
            decls = _block_declarations(block)
            for alias, info in decls.items():
                combined_names.add(alias)
                if info["display"]:
                    combined_names.add(info["display"])
            used, _ = _block_uses(block)
            combined_names.update(used)

        for name in sorted(expected - combined_names):
            all_issues.append(
                {
                    "kind": "missing_expected_actor",
                    "name": name,
                    "auto_fixable": False,
                    "detail": "Listed in --expected-actors but absent from every block",
                }
            )

    result = {
        "passed": len(all_issues) == 0,
        "target": str(target),
        "block_count": len(blocks),
        "issues": all_issues,
        "auto_fixable_count": sum(1 for i in all_issues if i.get("auto_fixable")),
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": args.output,
                "passed": result["passed"],
                "issue_count": len(all_issues),
                "auto_fixable_count": result["auto_fixable_count"],
            }
        )
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
