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


_ERD_ENTITY_RE = re.compile(r"^\s*(\w+)\s*\{", re.MULTILINE)
_MERMAID_ER_RE = re.compile(r"```mermaid.*?erDiagram(.*?)```", re.DOTALL)
_ENDPOINT_ROW_RE = re.compile(
    r"\|[^|\n]*\|\s*(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*\|\s*([^|\n]+?)\s*\|",
    re.IGNORECASE,
)


def existing_system_catalog(root: Path, hbc_output: Path, project_context: str | None) -> dict:
    """Best-effort AS-IS anchor catalog for brownfield grounding.

    Pulls deterministic anchors from the baseline artifacts Phase 0 (brownfield)
    produces: entities from the shared D-19 ER diagram, endpoints from the shared
    D-21 API spec. project-context.md is listed as a source (its canonical shape is
    tech-stack + rules, not an entity inventory, so nothing is parsed from it).
    Business flows are NOT parsed here — the BA reads D-06 AS-IS directly.

    Empty lists when the artifacts are absent; the caller surfaces a hint to run
    bmad-document-project / create the Phase 0 baselines so AS-IS is not thin.
    """
    sources: list[str] = []
    entities: list[str] = []
    endpoints: list[str] = []
    shared = hbc_output / "shared"

    if project_context:
        sources.append(project_context)

    erd_dir = shared / "erd"
    if erd_dir.exists():
        for d19 in sorted(erd_dir.glob("D-19-*.md")):
            sources.append(str(d19.relative_to(root)))
            try:
                text = d19.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for block in _MERMAID_ER_RE.findall(text):
                entities.extend(e for e in _ERD_ENTITY_RE.findall(block) if e != "erDiagram")

    api_dir = shared / "api"
    if api_dir.exists():
        for d21 in sorted(api_dir.glob("D-21-*.md")):
            sources.append(str(d21.relative_to(root)))
            try:
                text = d21.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for method, url in _ENDPOINT_ROW_RE.findall(text):
                token = f"{method.upper()} {url.strip()}"
                if url.strip() and not url.strip().lower().startswith("endpoint"):
                    endpoints.append(token)

    # de-dup, keep order
    entities = list(dict.fromkeys(entities))
    endpoints = list(dict.fromkeys(endpoints))

    catalog: dict = {
        "sources_present": sources,
        "entities": entities,
        "endpoints": endpoints,
    }
    if not entities and not endpoints:
        catalog["hint"] = (
            "AS-IS anchors are thin. For a brownfield project, run bmad-document-project "
            "and create the Phase 0 baselines (shared D-19 ERD / D-21 API) so requirements "
            "can be grounded against existing entities/endpoints."
        )
    return catalog


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

    result = {
        "state": state,
        "existing_d02": existing_d02,
        "source_docs": source_docs,
        "source_count": len(source_docs),
        "project_context": project_context,
        "brownfield": bool(project_context),
    }
    # Brownfield (project-context.md present) → attach the AS-IS anchor catalog the
    # BA uses to ground requirements. Greenfield: omitted (no AS-IS to reconcile).
    if project_context:
        result["existing_system"] = existing_system_catalog(root, hbc_output, project_context)
    return result


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
