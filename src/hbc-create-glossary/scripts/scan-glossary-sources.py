#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan project for glossary sources and extract term candidates.

Returns a compact JSON manifest for Stage 1 Prerequisites:
resume state, discovered sources, and candidate terms extracted
from D-02 requirements and project-context.md.
"""

import argparse
import json
import re
import sys
from pathlib import Path

TERM_PATTERNS = [
    (re.compile(r"“([^”]+)”"), "vi_quote"),
    (re.compile(r'"([A-Z][A-Za-z]{2,}(?:\s[A-Z][A-Za-z]+)*)"'), "en_capitalized"),
    (re.compile(r"\*\*([^*]{2,})\*\*"), "md_bold"),
    (re.compile(r"(?<!\*)_([^_]{2,})_(?!\*)"), "md_italic"),
]

ABBREVIATION_RE = re.compile(r"\b([A-Z]{2,6})\b")


def parse_frontmatter(path: Path) -> dict:
    """Extract frontmatter fields from a markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    fields: dict = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip().strip('"').strip("'")
    return fields


def extract_candidates(path: Path) -> list[dict]:
    """Extract potential glossary terms from a document with extraction method."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    seen: dict[str, dict] = {}

    for pattern, method in TERM_PATTERNS:
        for match in pattern.findall(text):
            if match not in seen:
                seen[match] = {"term": match, "method": method}

    for abbr in ABBREVIATION_RE.findall(text):
        if abbr not in seen:
            seen[abbr] = {"term": abbr, "method": "abbreviation"}

    return list(seen.values())


def scan_sources(project_root: str, explicit_sources: list[str] | None = None) -> dict:
    """Scan project for glossary sources and existing D-03."""
    root = Path(project_root)
    hbc_output = root / "_bmad-output"

    existing_d03: dict | None = None
    source_docs: list[dict] = []
    all_candidates: list[dict] = []

    search_dirs = [hbc_output / "planning-artifacts"] if hbc_output.exists() else []
    search_dirs.append(root)

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for path in search_dir.glob("D-03*"):
            if path.is_file():
                fm = parse_frontmatter(path)
                existing_d03 = {
                    "path": str(path.relative_to(root)),
                    "lastStep": fm.get("lastStep", ""),
                    "version": fm.get("version", ""),
                }
                break

    if explicit_sources:
        for src in explicit_sources:
            path = root / src if not Path(src).is_absolute() else Path(src)
            if path.is_file():
                rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
                source_docs.append({"path": rel, "name": path.name})
                all_candidates.extend(extract_candidates(path))
    else:
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for pattern in ["D-02*", "D-01*"]:
                for path in search_dir.glob(pattern):
                    if path.is_file():
                        rel = str(path.relative_to(root))
                        source_docs.append({"path": rel, "name": path.name})
                        all_candidates.extend(extract_candidates(path))

        for ctx in root.rglob("project-context.md"):
            rel = str(ctx.relative_to(root))
            source_docs.append({"path": rel, "name": ctx.name})
            all_candidates.extend(extract_candidates(ctx))
            break

    seen: dict[str, dict] = {}
    for c in all_candidates:
        if c["term"] not in seen:
            seen[c["term"]] = c
    unique_candidates = list(seen.values())

    state = "fresh"
    if existing_d03:
        if existing_d03.get("lastStep") == "complete":
            state = "update"
        else:
            state = "resume"

    return {
        "state": state,
        "existing_d03": existing_d03,
        "source_docs": source_docs,
        "source_count": len(source_docs),
        "raw_candidates": unique_candidates,
        "candidate_count": len(unique_candidates),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scan project for glossary sources and term candidates."
    )
    parser.add_argument(
        "--project-root", required=True, help="Project root directory"
    )
    parser.add_argument(
        "--sources", help="Comma-separated source file paths (skips auto-discovery)"
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()] if args.sources else None
    result = scan_sources(args.project_root, explicit_sources=sources)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0)


if __name__ == "__main__":
    main()
