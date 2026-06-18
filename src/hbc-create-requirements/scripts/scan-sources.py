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


_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
_MERMAID_ER_RE = re.compile(r"```mermaid.*?erDiagram(.*?)```", re.DOTALL)
_ERD_ENTITY_RE = re.compile(r"^\s*(\w+)\s*\{", re.MULTILINE)
# Mermaid ER relationship line — compositional cardinality (left + line + right),
# so an entity that appears ONLY in a relationship (no attribute block) is captured.
_ER_REL_RE = re.compile(
    r"^\s*(\w+)\s+(?:\|o|\|\||\}o|\}\|)(?:--|\.\.)(?:o\||\|\||o\{|\|\{)\s+(\w+)\s*:",
    re.MULTILINE,
)
_DETAIL_METHOD_RE = re.compile(r"\*\*Method:\*\*\s*`?([A-Za-z]+)", re.IGNORECASE)
_DETAIL_URL_RE = re.compile(r"\*\*URL:\*\*\s*`?(\S+)", re.IGNORECASE)


def _extract_entities(text: str) -> list[str]:
    ents: list[str] = []
    for block in _MERMAID_ER_RE.findall(text):
        ents.extend(e for e in _ERD_ENTITY_RE.findall(block) if e != "erDiagram")
        for left, right in _ER_REL_RE.findall(block):
            ents.extend([left, right])
    return ents


def _extract_endpoints(text: str) -> list[str]:
    """Endpoints from a D-21: the Endpoint List table (header-keyed, so column order
    / a missing leading column doesn't matter; English or configured-language headers)
    plus any `**Method:** / **URL:**` detail blocks."""
    out: list[str] = []
    pipe = [ln.strip() for ln in text.splitlines() if ln.strip().startswith("|")]
    for hi, line in enumerate(pipe):
        cells = [c.strip().lower() for c in line.strip("|").split("|")]
        mi = next((i for i, c in enumerate(cells) if "method" in c or "phương thức" in c), None)
        ei = next((i for i, c in enumerate(cells) if "endpoint" in c or "url" in c or "đường dẫn" in c), None)
        if mi is None or ei is None:
            continue
        for dl in pipe[hi + 1:]:
            dc = [c.strip() for c in dl.strip("|").split("|")]
            if set("".join(dc)) <= {"-", " ", ":"}:
                continue
            if mi < len(dc) and ei < len(dc):
                method, url = dc[mi].upper(), dc[ei]
                if method in _HTTP_METHODS and url:
                    out.append(f"{method} {url}")
        break  # only the first method+endpoint table is the Endpoint List
    methods = _DETAIL_METHOD_RE.findall(text)
    urls = _DETAIL_URL_RE.findall(text)
    for m, u in zip(methods, urls):
        if m.upper() in _HTTP_METHODS:
            out.append(f"{m.upper()} {u}")
    return out


def existing_system_catalog(root: Path, hbc_output: Path, project_context: str | None) -> dict:
    """Best-effort AS-IS anchor catalog for brownfield grounding: entities from the
    shared D-19 ER diagram, endpoints from the shared D-21 API spec, plus the AS-IS
    source docs present. The `hint` names which baseline is missing so the caller can
    route to the right Phase 0 doc (a thin catalog misleads the BA into thinking an
    existing entity/endpoint is absent)."""
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
                entities.extend(_extract_entities(d19.read_text(encoding="utf-8")))
            except (OSError, UnicodeDecodeError):
                continue

    api_dir = shared / "api"
    if api_dir.exists():
        for d21 in sorted(api_dir.glob("D-21-*.md")):
            sources.append(str(d21.relative_to(root)))
            try:
                endpoints.extend(_extract_endpoints(d21.read_text(encoding="utf-8")))
            except (OSError, UnicodeDecodeError):
                continue

    entities = list(dict.fromkeys(entities))
    endpoints = list(dict.fromkeys(endpoints))

    catalog: dict = {
        "sources_present": sources,
        "entities": entities,
        "endpoints": endpoints,
    }
    # Per-baseline hint: fire when EITHER anchor set is empty (not only when both),
    # so a project with D-19 but no D-21 (a common mid-Phase-0 state) is still told.
    missing = []
    if not entities:
        missing.append("entities (D-19 ERD)")
    if not endpoints:
        missing.append("endpoints (D-21 API)")
    if missing:
        # Generic framing (DF-6): point at the documented AS-IS as the anchor source
        # for ANY project type; structured D-19/D-21 baselines are one option, named
        # as a sub-note (kept so the BA still sees which is absent).
        catalog["hint"] = (
            "No structured anchors yet — derive existing-system anchors from the "
            "documented AS-IS in `sources_present` (the modules/services/components "
            "named in project-context.md or bmad-document-project docs). If nothing is "
            "documented, run bmad-document-project. (Structured baselines are one option "
            "for DB/API products; missing: " + "; ".join(missing) + ".)"
        )
    return catalog


# Markers of an existing codebase (dependency manifests). Their presence WITHOUT a
# project-context.md suggests a brownfield project that skipped Phase 0 — surfaced as
# `brownfield_suspected` so the skill can nudge, rather than silently going greenfield.
_CODE_MARKERS = (
    "package.json", "pyproject.toml", "setup.py", "go.mod", "pom.xml", "build.gradle",
    "composer.json", "Gemfile", "requirements.txt", "Cargo.toml", "pubspec.yaml",
)


def _has_existing_code(root: Path) -> bool:
    if any((root / m).exists() for m in _CODE_MARKERS):
        return True
    return any(root.glob("*.csproj")) or any(root.glob("*.sln"))


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
        # Existing codebase but no project-context.md → likely a brownfield project
        # that skipped Phase 0; the skill nudges to run [PI]/document-project instead
        # of grounding-less greenfield. Only meaningful when not already brownfield.
        "brownfield_suspected": (not project_context) and _has_existing_code(root),
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
