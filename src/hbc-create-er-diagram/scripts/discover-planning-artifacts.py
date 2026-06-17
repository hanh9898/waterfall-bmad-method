#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stage 1 pre-pass: scan planning_artifacts and emit JSON inventory.

Resolves PRD (whole-doc or sharded), Architecture, UX, use-case, D-20
table definitions, and research docs. Supports English- and Japanese-titled
HBC files. Verifies the configured er_diagram_template exists. Optionally
emits resume-state for Stage 1a when --primary (the output document path) is
given, reading the peer .decision-log.md beside it.

Brownfield ingest: when --project-knowledge <dir> is given (the
bmad-document-project output root), the script ALSO enumerates that root's
index.md, the project docs beneath it, and any existing DB schema files
(*.sql / *schema*.{md,json,yaml,prisma} / ORM model dirs). These feed the
D-19 baseline so it reflects the real DB, not just the PRD. Greenfield runs
omit the flag and are unaffected.

Exit codes:
  0  inventory produced, no fatal issues
  1  template missing or planning_artifacts unreadable (skill should HALT
     interactive or return `blocked` headless)
  2  argument or filesystem error (script bug)
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


PRD_GLOBS = ["*prd*.md", "*PRD*.md"]
ARCH_GLOBS = [
    "*architecture*.md",
    "D-09*.md",
    "D-08*.md",
]
UX_GLOBS = ["*ux*.md", "*UX*.md", "*ui*.md", "*UI*.md"]
USE_CASE_GLOBS = [
    "*use-case*.md",
    "*use_case*.md",
    "D-04*.md",
    "D-05*.md",
]
TABLE_DEF_GLOBS = [
    "D-20*.md",
    "*table-def*.md",
    "*table_def*.md",
]
RESEARCH_GLOBS = ["research/*.md", "research/**/*.md"]
# Brownfield: existing DB schema artifacts under the bmad-document-project root.
SCHEMA_GLOBS = [
    "**/*.sql",
    "**/*schema*.md",
    "**/*schema*.json",
    "**/*schema*.yaml",
    "**/*schema*.yml",
    "**/*.prisma",
    "**/schema.rb",
    "**/models/**/*.py",
    "**/entities/**/*.ts",
]


def _make_entry(p: Path) -> dict[str, object]:
    return {"path": str(p), "is_symlink": p.is_symlink()}


def _unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = str(p.absolute())
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _glob(root: Path, patterns: list[str]) -> list[Path]:
    found: list[Path] = []
    for pat in patterns:
        found.extend(root.glob(pat))
    return _unique_paths(sorted(found))


def _is_sharded(prd_path: Path) -> bool:
    if prd_path.is_dir():
        return (prd_path / "index.md").exists()
    parent_index = prd_path.parent / prd_path.stem / "index.md"
    return parent_index.exists()


def _enumerate_shards(prd_path: Path) -> list[dict[str, object]]:
    """Return entries for every shard of a sharded PRD."""
    if prd_path.is_dir():
        index = prd_path / "index.md"
        shard_dir = prd_path
    else:
        shard_dir = prd_path.parent / prd_path.stem
        index = shard_dir / "index.md"

    if not index.exists():
        return []

    shard_paths: list[Path] = []
    text = index.read_text(encoding="utf-8", errors="replace")
    for match in re.finditer(r"\]\(([^)]+\.md)\)", text):
        rel = match.group(1).strip()
        candidate = index.parent / rel
        if candidate.exists() and candidate.suffix == ".md" and candidate.name != "index.md":
            shard_paths.append(candidate)

    if not shard_paths:
        for f in sorted(shard_dir.glob("**/*.md")):
            if f.name != "index.md":
                shard_paths.append(f)

    return [_make_entry(p) for p in _unique_paths(shard_paths)]


def _classify_prd(prd_path: Path) -> dict[str, object]:
    entry = _make_entry(prd_path)
    entry["is_sharded"] = _is_sharded(prd_path)
    entry["shard_paths"] = _enumerate_shards(prd_path) if entry["is_sharded"] else []
    return entry


def _scan_project_knowledge(pk_root: Path) -> dict[str, object]:
    """Brownfield ingest: enumerate the bmad-document-project output.

    Returns the project index.md, the project docs beneath the root, and any
    existing DB schema artifacts. These give the D-19 baseline a view of the
    real database rather than relying on the PRD alone."""
    out: dict[str, object] = {
        "root": str(pk_root),
        "exists": pk_root.exists(),
        "index": None,
        "docs": [],
        "schema": [],
    }
    if not pk_root.exists():
        return out

    index = pk_root / "index.md"
    if index.exists():
        out["index"] = _make_entry(index)

    docs = [
        p
        for p in sorted(pk_root.glob("**/*.md"))
        if p.name != "index.md"
    ]
    out["docs"] = [_make_entry(p) for p in _unique_paths(docs)]
    out["schema"] = [_make_entry(p) for p in _glob(pk_root, SCHEMA_GLOBS)]
    return out


def _extract_resume_state(primary: Path) -> dict[str, object]:
    """Read the primary document + its peer decision log and summarise
    resume-relevant state for Stage 1a. `primary` is the single output FILE
    in planning_artifacts; the decision log is its sibling .decision-log.md."""
    log = primary.parent / ".decision-log.md"
    state: dict[str, object] = {
        "primary": str(primary),
        "primary_exists": primary.exists(),
        "decision_log_exists": log.exists(),
        "primary_steps_completed": [],
        "primary_last_step": None,
        "primary_updated": None,
        "last_session_summary": None,
    }

    if primary.exists():
        text = primary.read_text(encoding="utf-8", errors="replace")
        fm_match = re.match(r"---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
        if fm_match:
            fm = fm_match.group(1)
            steps_match = re.search(r"^stepsCompleted:\s*\[(.*?)\]\s*$", fm, re.MULTILINE)
            if steps_match:
                items = [s.strip().strip("\"'") for s in steps_match.group(1).split(",") if s.strip()]
                state["primary_steps_completed"] = items
            last_step_match = re.search(r"^lastStep:\s*[\"']?(.*?)[\"']?\s*$", fm, re.MULTILINE)
            if last_step_match:
                state["primary_last_step"] = last_step_match.group(1).strip()
            updated_match = re.search(r"^updated:\s*[\"']?(.*?)[\"']?\s*$", fm, re.MULTILINE)
            if updated_match:
                state["primary_updated"] = updated_match.group(1).strip()

    if log.exists():
        text = log.read_text(encoding="utf-8", errors="replace")
        sessions = list(
            re.finditer(
                r"^##\s+([^\n]*\d{4}-\d{2}-\d{2}[^\n]*)$",
                text,
                re.MULTILINE,
            )
        )
        if sessions:
            last = sessions[-1]
            heading = last.group(1).strip()
            after = text[last.end():].lstrip()
            summary_first = after.split("\n", 1)[0].strip()
            state["last_session_summary"] = f"{heading} — {summary_first}" if summary_first else heading

    steps: list[str] = list(state["primary_steps_completed"])  # type: ignore[arg-type]
    state["fresh_reason"] = None
    if not state["primary_exists"]:
        state["recommended_intent"] = "Fresh"
        state["fresh_reason"] = "no_primary"
    elif not steps:
        state["recommended_intent"] = "Fresh"
        state["fresh_reason"] = "crashed_no_progress"
    elif "stage-5" in steps:
        state["recommended_intent"] = "Update"
    elif "stage-1" in steps:
        state["recommended_intent"] = "Resume"
    else:
        state["recommended_intent"] = "Fresh"
        state["fresh_reason"] = "stale_artifact"

    return state


def main() -> int:
    doc = __doc__ or ""
    parser = argparse.ArgumentParser(description=doc.split("\n\n")[0])
    parser.add_argument("planning_artifacts", help="Path to planning_artifacts directory")
    parser.add_argument(
        "--template-path",
        required=True,
        help="Resolved path to er_diagram_template (Stage 1 will refuse to start if missing)",
    )
    parser.add_argument(
        "--project-knowledge",
        default=None,
        help="Optional (brownfield): path to the bmad-document-project output root. When provided, the script ALSO ingests its index.md, project docs, and existing DB schema files into the source inventory so the D-19 baseline reflects the real database. Omit for greenfield.",
    )
    parser.add_argument(
        "--primary",
        default=None,
        help="Optional: path to the single output document. When provided, the script emits resume_state for Stage 1a, reading the peer .decision-log.md beside it.",
    )
    parser.add_argument("-o", "--output", required=True, help="JSON output path")
    args = parser.parse_args()

    artifacts = Path(args.planning_artifacts)
    template = Path(args.template_path)

    result: dict[str, object] = {
        "planning_artifacts": str(artifacts),
        "template_path": str(template),
        "template_exists": template.exists(),
        "artifacts_dir_exists": artifacts.exists(),
        "prd": [],
        "architecture": [],
        "ux": [],
        "use_case": [],
        "table_definitions": [],
        "research": [],
        "project_knowledge": None,
    }

    fatal = False

    if not template.exists():
        result["fatal"] = "template_missing"
        fatal = True

    if not artifacts.exists():
        result["artifacts_status"] = "directory_missing"
    else:
        prd_files = _glob(artifacts, PRD_GLOBS)
        prd_name_re = re.compile(r"\bprd\b", re.IGNORECASE)
        prd_dirs = [
            d
            for d in artifacts.iterdir()
            if d.is_dir() and prd_name_re.search(d.name) and (d / "index.md").exists()
        ]
        result["prd"] = [_classify_prd(p) for p in _unique_paths(prd_files + prd_dirs)]
        result["architecture"] = [_make_entry(p) for p in _glob(artifacts, ARCH_GLOBS)]
        result["ux"] = [_make_entry(p) for p in _glob(artifacts, UX_GLOBS)]
        result["use_case"] = [_make_entry(p) for p in _glob(artifacts, USE_CASE_GLOBS)]
        result["table_definitions"] = [_make_entry(p) for p in _glob(artifacts, TABLE_DEF_GLOBS)]
        result["research"] = [_make_entry(p) for p in _glob(artifacts, RESEARCH_GLOBS)]

    if args.project_knowledge:
        result["project_knowledge"] = _scan_project_knowledge(Path(args.project_knowledge))

    if args.primary:
        result["resume_state"] = _extract_resume_state(Path(args.primary))

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": args.output, "fatal": result.get("fatal", None)}))
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
