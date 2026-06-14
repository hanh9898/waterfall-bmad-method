#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan project for HBC source documents and existing D-02 artifacts.

Returns a compact JSON manifest for Stage 1 Prerequisites:
resume state, discovered source documents, and project context path.
"""

import argparse
import json
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

HBC_DOC_PATTERNS = [
    "D-01*", "D-02*", "D-03*", "D-06*",
    "project-context.md", "*.interview.*",
]

FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---", re.DOTALL
)


def parse_frontmatter(path: Path) -> dict:
    """Extract YAML-like frontmatter fields from a markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}

    fields: dict = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip().strip('"').strip("'")
    return fields


def scan_sources(project_root: str) -> dict:
    """Scan project for source documents and D-02 state."""
    root = Path(project_root)
    hbc_output = root / "_bmad-output"

    existing_d02: dict | None = None
    source_docs: list[dict] = []
    project_context: str | None = None

    for ctx in root.rglob("project-context.md"):
        project_context = str(ctx.relative_to(root))
        break

    search_dirs = [root, hbc_output / "planning-artifacts"] if hbc_output.exists() else [root]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for pattern in HBC_DOC_PATTERNS:
            for path in search_dir.glob(pattern):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(root))

                if path.name.startswith("D-02"):
                    fm = parse_frontmatter(path)
                    existing_d02 = {
                        "path": rel,
                        "lastStep": fm.get("lastStep", ""),
                        "version": fm.get("version", ""),
                        "status": fm.get("status", ""),
                    }
                elif rel not in [d["path"] for d in source_docs]:
                    source_docs.append({
                        "path": rel,
                        "type": path.suffix.lstrip("."),
                        "name": path.name,
                    })

    state = "fresh"
    if existing_d02:
        if existing_d02.get("lastStep") == "complete":
            state = "update"
        else:
            state = "resume"

    return {
        "state": state,
        "existing_d02": existing_d02,
        "source_docs": source_docs,
        "source_count": len(source_docs),
        "project_context": project_context,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scan project for HBC source documents."
    )
    parser.add_argument(
        "--project-root", required=True, help="Project root directory"
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    result = scan_sources(args.project_root)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0)


if __name__ == "__main__":
    main()
