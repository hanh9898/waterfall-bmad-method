#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Phase-0 baseline scan for hbc-project-init.

Deterministic structure-only scan. Reports:
  - shared deliverable presence (D-12, D-03, D-19 baseline, D-21 baseline, constitution)
  - project-context.md and bmad-document-project knowledge presence
  - brownfield vs greenfield (codebase presence outside the tooling/output dirs)
  - legacy v1 (flat) layout detection -> recommend hbc-migrate first
  - applicability-catalog load (the canonical node-set Phase 0 must seed)
  - drift on re-invocation: which present deliverables look stale vs the catalog /
    config (B15-1) -- structural signals only; the meaning of "stale" is judged by
    the LLM layer.

All meaning (is this convention right? does the catalog node apply?) is OUT OF
SCOPE -- this script does structure only and prints JSON to stdout.
"""

import argparse
import glob
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
FIELD_RE = re.compile(r"^(\w+)\s*:\s*(.+)$", re.MULTILINE)

# Dirs that are tooling/output, NOT first-party source code.
NON_SOURCE_DIRS = {"_bmad", "_bmad-output", "docs", ".git", ".claude",
                   "node_modules", ".venv", "venv", "__pycache__"}
SOURCE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".php", ".java", ".go",
               ".rb", ".rs", ".vue", ".kt", ".cs", ".xml"}


def read_frontmatter(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(8192)
    except (OSError, UnicodeDecodeError):
        return {}
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}
    fields = {}
    for m in FIELD_RE.finditer(match.group(1)):
        fields[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fields


def first_match(*patterns):
    """Return the first existing path matching any glob pattern, else None."""
    for pattern in patterns:
        matches = sorted(glob.glob(pattern, recursive=True))
        for m in matches:
            if os.path.isfile(m):
                return m
    return None


def detect_brownfield(project_root):
    """Greenfield = no first-party source outside the tooling/output dirs."""
    try:
        entries = os.listdir(project_root)
    except OSError:
        return False
    for entry in entries:
        if entry in NON_SOURCE_DIRS or entry.startswith("."):
            continue
        full = os.path.join(project_root, entry)
        if os.path.isfile(full):
            if os.path.splitext(entry)[1].lower() in SOURCE_EXTS:
                return True
        elif os.path.isdir(full):
            # any source file anywhere under this top-level dir
            for _root, dirs, files in os.walk(full):
                dirs[:] = [d for d in dirs if d not in NON_SOURCE_DIRS
                           and not d.startswith(".")]
                for fn in files:
                    if os.path.splitext(fn)[1].lower() in SOURCE_EXTS:
                        return True
    return False


def detect_legacy_v1(output_folder):
    """v1 = flat planning-artifacts / traceability WITHOUT a features/ dir."""
    planning_flat = glob.glob(os.path.join(output_folder, "planning-artifacts", "D-*"))
    matrix_flat = glob.glob(os.path.join(output_folder, "traceability", "matrix*"))
    has_features = os.path.isdir(os.path.join(output_folder, "features"))
    return bool(planning_flat or matrix_flat) and not has_features


def load_catalog(catalog_path):
    """Load the applicability-catalog. Prefer PyYAML; fall back to a tiny
    deliverables-block parser so the script stays stdlib-only and never crashes
    Phase 0 just because PyYAML is absent."""
    if not catalog_path or not os.path.isfile(catalog_path):
        return {"loaded": False, "path": catalog_path, "deliverables": [], "facets": []}
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return {"loaded": False, "path": catalog_path, "deliverables": [], "facets": []}

    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text) or {}
        delivs = [
            {"id": d.get("id"), "name": d.get("name"), "phase": d.get("phase"),
             "scope": d.get("scope"), "default_applicability": d.get("default_applicability"),
             "owner_skill": d.get("owner_skill")}
            for d in (data.get("deliverables") or [])
        ]
        return {
            "loaded": True,
            "path": catalog_path,
            "schema_version": data.get("schema_version"),
            "facets": data.get("facets") or [],
            "deliverables": delivs,
        }
    except Exception:
        # stdlib fallback: parse each `{ id: D-xx, ... phase: N ... }` line
        delivs = []
        for m in re.finditer(r"\{\s*id:\s*([\w-]+).*?phase:\s*(\d+).*?\}", text):
            delivs.append({"id": m.group(1), "phase": int(m.group(2))})
        facets = re.findall(r"^\s*-\s*(has-[\w-]+)", text, re.MULTILINE)
        sv = re.search(r'schema_version:\s*"?([\d.]+)"?', text)
        return {
            "loaded": True,
            "path": catalog_path,
            "schema_version": sv.group(1) if sv else None,
            "facets": facets,
            "deliverables": delivs,
            "parser": "stdlib-fallback",
        }


def find_catalog(skill_root, explicit):
    if explicit and os.path.isfile(explicit):
        return explicit
    candidates = []
    if skill_root:
        candidates.append(os.path.join(
            os.path.dirname(skill_root.rstrip("/\\")),
            "hbc-shared", "references", "deliverable-catalog.yaml"))
        # installed runtime layout: .claude/skills/hbc-shared/...
        candidates.append(os.path.join(
            skill_root, "..", "hbc-shared", "references", "deliverable-catalog.yaml"))
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.normpath(c)
    return explicit  # may be None / non-existent; load_catalog handles it


def scan(project_root, output_folder, skill_root=None, catalog_path=None,
         project_knowledge=None):
    shared = os.path.join(output_folder, "shared")

    deliverables = {
        "D-12": first_match(os.path.join(shared, "coding-standards", "D-12*")),
        "D-03": first_match(os.path.join(shared, "glossary", "D-03*")),
        "D-19": first_match(os.path.join(shared, "erd", "D-19*")),
        "D-21": first_match(os.path.join(shared, "api", "D-21*")),
        "constitution": first_match(os.path.join(shared, "constitution.md"),
                                    os.path.join(shared, "constitution", "constitution.md")),
    }

    present, missing, frontmatters = [], [], {}
    for did, path in deliverables.items():
        if path:
            present.append(did)
            frontmatters[did] = read_frontmatter(path)
        else:
            missing.append(did)

    project_context_path = first_match(
        os.path.join(project_root, "project-context.md"),
        os.path.join(project_root, "_bmad", "project-context.md"),
        os.path.join(project_root, "**", "project-context.md"),
    )
    knowledge_index = None
    if project_knowledge:
        idx = os.path.join(project_knowledge, "index.md")
        knowledge_index = idx if os.path.isfile(idx) else None

    brownfield = detect_brownfield(project_root)
    legacy_v1 = detect_legacy_v1(output_folder)

    resolved_catalog = find_catalog(skill_root, catalog_path)
    catalog = load_catalog(resolved_catalog)

    # Drift signals (B15-1) — structural only. On a re-run, a present deliverable
    # whose frontmatter lacks lastStep=complete, or has no semanticReview.status
    # passed, is flagged for the LLM layer to judge whether an update is due.
    drift = []
    for did in present:
        fm = frontmatters.get(did, {})
        if did == "constitution":
            if not fm:
                drift.append({"deliverable": did, "signal": "no_frontmatter"})
            elif fm.get("lastStep", "") != "complete":
                drift.append({"deliverable": did, "signal": "incomplete",
                              "lastStep": fm.get("lastStep", "")})
        else:
            if fm.get("lastStep", "") not in ("complete", ""):
                drift.append({"deliverable": did, "signal": "incomplete",
                              "lastStep": fm.get("lastStep", "")})

    is_rerun = bool(present)  # at least one shared deliverable already exists

    return {
        "project_type": "brownfield" if brownfield else "greenfield",
        "is_rerun": is_rerun,
        "legacy_v1_layout": legacy_v1,
        "project_context_path": project_context_path,
        "project_context": "present" if project_context_path else "missing",
        "documented": bool(knowledge_index),
        "knowledge_index": knowledge_index,
        "shared_dir": shared,
        "deliverables": {did: {"present": did in present, "path": p}
                         for did, p in deliverables.items()},
        "present": present,
        "missing": missing,
        "frontmatters": frontmatters,
        "drift": drift,
        "catalog": catalog,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Phase-0 baseline scan for hbc-project-init.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-folder", required=True,
                        help="HBC output root (typically {project-root}/_bmad-output)")
    parser.add_argument("--skill-root",
                        help="This skill's installed dir (to locate the shared catalog)")
    parser.add_argument("--catalog-path",
                        help="Explicit path to deliverable-catalog.yaml (overrides auto-locate)")
    parser.add_argument("--project-knowledge",
                        help="bmad-document-project output dir (brownfield); greenfield: omit")
    parser.add_argument("-o", "--output", help="Write JSON to file instead of stdout")
    args = parser.parse_args()

    result = scan(args.project_root, args.output_folder, args.skill_root,
                  args.catalog_path, args.project_knowledge)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
