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

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
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


def scan_sources(
    project_root: str,
    explicit_sources: list[str] | None = None,
    output_folder: str = "_bmad-output",
    project_knowledge: str | None = None,
) -> dict:
    """Scan project for glossary sources and existing D-03.

    D-03 is a SHARED deliverable written to {output_folder}/shared/glossary/.
    Resolve the existing-D-03 target there (with a back-compat fallback to the
    old flat location and project root). Source docs (D-02 etc.) may be
    per-feature or project-level, so the whole _bmad-output tree (plus root) is
    searched for them.

    Brownfield (#7): when `project_knowledge` (bmad-document-project output, e.g.
    {project-root}/docs) is provided, its domain docs are ingested as additional
    glossary sources so D-03 terms derive from the REAL codebase domain, not just
    project-context.md. Greenfield (dir absent) is a no-op. `--sources` still
    skips ALL auto-discovery, including project-knowledge, for back-compat.
    """
    root = Path(project_root)
    out_root = Path(output_folder) if Path(output_folder).is_absolute() else root / output_folder
    shared_glossary = out_root / "shared" / "glossary"

    existing_d03: dict | None = None
    source_docs: list[dict] = []
    all_candidates: list[dict] = []

    # Detect existing D-03 in the SHARED glossary dir first; keep back-compat
    # fallbacks to the old flat planning-artifacts path and the project root.
    d03_search_dirs = [
        shared_glossary,
        out_root / "planning-artifacts",
        root,
    ]
    for search_dir in d03_search_dirs:
        if not search_dir.exists():
            continue
        for path in sorted(search_dir.glob("D-03*")):
            if path.is_file():
                fm = parse_frontmatter(path)
                rel = (
                    str(path.relative_to(root))
                    if path.is_relative_to(root)
                    else str(path)
                )
                existing_d03 = {
                    "path": rel,
                    "lastStep": fm.get("lastStep", ""),
                    "version": fm.get("version", ""),
                }
                break
        if existing_d03:
            break

    # Source docs may live anywhere under _bmad-output (per-feature or
    # project-level) or at the project root — walk the whole tree.
    if out_root.exists():
        search_dirs = sorted({p.parent for p in out_root.rglob("*") if p.is_file()})
    else:
        search_dirs = []
    search_dirs.append(root)

    if explicit_sources:
        for src in explicit_sources:
            path = root / src if not Path(src).is_absolute() else Path(src)
            if path.is_file():
                rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
                source_docs.append({"path": rel, "name": path.name})
                all_candidates.extend(extract_candidates(path))
    else:
        seen_src: set[str] = set()
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            for pattern in ["D-02*", "D-01*"]:
                for path in sorted(search_dir.glob(pattern)):
                    if path.is_file():
                        rel = str(path.relative_to(root))
                        if rel in seen_src:
                            continue
                        seen_src.add(rel)
                        source_docs.append({"path": rel, "name": path.name})
                        all_candidates.extend(extract_candidates(path))

        for ctx in root.rglob("project-context.md"):
            rel = str(ctx.relative_to(root))
            source_docs.append({"path": rel, "name": ctx.name})
            all_candidates.extend(extract_candidates(ctx))
            break

        # Brownfield (#7): ingest bmad-document-project domain docs as additional
        # glossary sources. Greenfield (no project_knowledge dir) is a no-op.
        if project_knowledge:
            pk_root = (
                Path(project_knowledge)
                if Path(project_knowledge).is_absolute()
                else root / project_knowledge
            )
            if pk_root.is_dir():
                for path in sorted(pk_root.rglob("*.md")):
                    if not path.is_file():
                        continue
                    rel = (
                        str(path.relative_to(root))
                        if path.is_relative_to(root)
                        else str(path)
                    )
                    if rel in seen_src:
                        continue
                    seen_src.add(rel)
                    source_docs.append({"path": rel, "name": path.name})
                    all_candidates.extend(extract_candidates(path))

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
    parser.add_argument(
        "--output-folder",
        default="_bmad-output",
        help="HBC output folder (default: _bmad-output); D-03 resolves under {output-folder}/shared/glossary",
    )
    parser.add_argument(
        "--project-knowledge",
        help="bmad-document-project output dir (brownfield domain docs); typically "
        "{project-root}/docs. Ingested as extra glossary sources. Greenfield: omit.",
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    sources = [s.strip() for s in args.sources.split(",") if s.strip()] if args.sources else None
    result = scan_sources(
        args.project_root,
        explicit_sources=sources,
        output_folder=args.output_folder,
        project_knowledge=args.project_knowledge,
    )

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0)


if __name__ == "__main__":
    main()
