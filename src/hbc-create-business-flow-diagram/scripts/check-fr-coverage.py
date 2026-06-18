#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stage 4 validator: extract FR-* identifiers from PRD and the D-06 output,
return covered / uncovered / phantom sets.

  covered    = FR ids referenced in both PRD and D-06
  uncovered  = FR ids in PRD but not referenced in any D-06 flow
  phantom    = FR ids in D-06 but not declared in PRD

When `--prd` points to a directory the script walks markdown recursively,
skipping common "stale" folders (archive, archived, notes, scratch, drafts,
.git, node_modules) so retired PRD versions don't pollute the uncovered set.

CLI shape matches the sibling validator scripts:
  --d06 <path>       D-06 markdown file (the validation target)
  --prd <path>       PRD source — file or directory. Repeatable for sharded
                     PRDs or multiple sources.
  -o / --output      JSON sink

Exit codes:
  0  no uncovered, no phantom
  1  coverage gaps found
  2  PRD or D-06 file unreadable / argument error
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


DEFAULT_FR_PATTERN = r"\b(N?FR-[0-9]+(?:\.[0-9]+)*)\b"
FR_RE = re.compile(DEFAULT_FR_PATTERN)

# Directories never walked for FR extraction.
EXCLUDE_DIRS: frozenset[str] = frozenset(
    {"archive", "archived", "old", "notes", "scratch", "drafts", ".git", "node_modules", "__pycache__"}
)


def _read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _extract_ids(text: str) -> set[str]:
    return set(m.group(1) for m in FR_RE.finditer(text))


def _walk_md(root: Path) -> list[Path]:
    """rglob('*.md') with EXCLUDE_DIRS pruned out of the path."""
    out: list[Path] = []
    for f in root.rglob("*.md"):
        parts = {part.lower() for part in f.relative_to(root).parts[:-1]}
        if parts & {d.lower() for d in EXCLUDE_DIRS}:
            continue
        out.append(f)
    return sorted(out)


def _gather_prd_ids(prd_paths: list[Path]) -> tuple[set[str], list[str]]:
    """Return (FR id set, list of files actually read)."""
    ids: set[str] = set()
    read: list[str] = []
    for p in prd_paths:
        if not p.exists():
            continue
        if p.is_dir():
            for f in _walk_md(p):
                ids |= _extract_ids(_read_text(f))
                read.append(str(f))
        else:
            ids |= _extract_ids(_read_text(p))
            read.append(str(p))
    return ids, read


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--prd",
        required=True,
        action="append",
        help="PRD file or directory. Repeat for sharded PRDs or multiple sources.",
    )
    parser.add_argument(
        "--d06",
        required=True,
        help="Path to D-06 markdown file (the validation target).",
    )
    parser.add_argument("-o", "--output", required=True, help="JSON output path")
    parser.add_argument(
        "--pattern",
        default=DEFAULT_FR_PATTERN,
        help="Regex for requirement identifiers (default: FR-*/NFR-*). Must contain one capture group.",
    )
    args = parser.parse_args()

    global FR_RE
    # _extract_ids reads group(1); a pattern that fails to compile or has no
    # capture group would crash with no output. Validate and report cleanly (exit 2).
    try:
        FR_RE = re.compile(args.pattern)
    except re.error as e:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps({"passed": False, "error": "bad_pattern", "detail": str(e)}),
            encoding="utf-8",
        )
        return 2
    if FR_RE.groups < 1:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps({"passed": False, "error": "bad_pattern",
                        "detail": "--pattern must contain exactly one capture group"}),
            encoding="utf-8",
        )
        return 2

    prd_paths = [Path(p) for p in args.prd]
    d06 = Path(args.d06)

    if not d06.exists():
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps({"passed": False, "error": "d06_missing", "path": str(d06)}),
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

    prd_ids, prd_files_read = _gather_prd_ids(prd_paths)
    d06_ids = _extract_ids(_read_text(d06))

    covered = sorted(prd_ids & d06_ids)
    uncovered = sorted(prd_ids - d06_ids)
    phantom = sorted(d06_ids - prd_ids)

    vacuous = len(prd_ids) == 0 and len(d06_ids) == 0

    result = {
        "passed": not uncovered and not phantom,
        "vacuous": vacuous,
        "prd_paths": [str(p) for p in prd_paths],
        "prd_files_read": prd_files_read,
        "d06_path": str(d06),
        "covered": covered,
        "uncovered": uncovered,
        "phantom": phantom,
        "totals": {
            "prd_ids": len(prd_ids),
            "d06_ids": len(d06_ids),
            "covered": len(covered),
            "uncovered": len(uncovered),
            "phantom": len(phantom),
        },
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    summary: dict[str, object] = {
        "output": args.output,
        "passed": result["passed"],
        "covered": len(covered),
        "uncovered": len(uncovered),
        "phantom": len(phantom),
    }
    if vacuous:
        summary["vacuous"] = True
    print(json.dumps(summary))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
