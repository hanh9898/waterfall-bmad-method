#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stage 1 pre-pass: scan planning_artifacts and emit JSON inventory.

Resolves PRD (whole-doc or sharded), UX, use-case (D-04/D-05), and research
docs. Supports English- and Japanese-titled HBC files (`要件定義書*.md`,
`企画書*.md`, `ユースケース*.md`, `画面*.md`). Verifies the configured
business_flow_template exists. Optionally emits resume-state for Stage 1a
when a workspace path is given.

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
from pathlib import Path


# Requirement-source names. D-02 is HBC's canonical requirement doc (C-4: was
# previously missed because only "PRD"-named files were recognised). English +
# Vietnamese first; legacy Japanese names kept for backward compatibility only.
PRD_GLOBS = [
    "D-02*.md",
    "*prd*.md", "*PRD*.md",
    "*requirements*.md", "*requirement*.md",
    "*yêu cầu*.md", "*yeu cau*.md",
    "*要件定義書*.md", "*要件*.md", "*企画書*.md",
]
UX_GLOBS = ["*ux*.md", "*UX*.md", "*ui*.md", "*UI*.md", "*画面*.md"]
USE_CASE_GLOBS = [
    "*use-case*.md",
    "*use_case*.md",
    "D-04*.md",
    "D-05*.md",
    "*ユースケース*.md",
]
RESEARCH_GLOBS = ["research/*.md", "research/**/*.md"]


def _make_entry(p: Path) -> dict[str, object]:
    return {"path": str(p), "is_symlink": p.is_symlink()}


def _unique_paths(paths: list[Path]) -> list[Path]:
    # Note: do not resolve() — that follows symlinks silently. Compare by
    # the absolute path keeping the symlink visible so callers see it as
    # a symlink in the output JSON.
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
        candidate = (index.parent / rel)
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


AS_IS_RE = re.compile(r"AS-IS|現状|current\s+state", re.IGNORECASE)


def _check_as_is(prd_entries: list[dict[str, object]]) -> dict[str, object]:
    """Scan PRD files for AS-IS / 現状 / 'current state' markers."""
    matches: list[dict[str, str]] = []
    for entry in prd_entries:
        p = Path(str(entry["path"]))
        shards = entry.get("shard_paths", [])
        paths_to_scan = [p] if not shards else [Path(str(s["path"])) for s in shards]
        for sp in paths_to_scan:
            try:
                text = sp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in AS_IS_RE.finditer(text):
                matches.append({"file": str(sp), "match": m.group(0)})
    return {"has_as_is": len(matches) > 0, "matches": matches}


def _read_first_match(path: Path, pattern: re.Pattern[str]) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = pattern.search(text)
    return match.group(1) if match else None


def _extract_resume_state(workspace: Path) -> dict[str, object]:
    """Read the primary + decision log inside an existing workspace and
    summarise resume-relevant state for Stage 1a."""
    primary = workspace / "D-06-business-flow-diagram.md"
    log = workspace / ".decision-log.md"
    state: dict[str, object] = {
        "workspace": str(workspace),
        "primary_exists": primary.exists(),
        "decision_log_exists": log.exists(),
        "primary_steps_completed": [],
        "primary_last_step": None,
        "primary_updated": None,
        "last_session_summary": None,
        "mode_from_prior_session": None,
    }

    if primary.exists():
        text = primary.read_text(encoding="utf-8", errors="replace")
        # Read YAML-style frontmatter at file head (between two `---` markers).
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
        # Last H2 heading containing a YYYY-MM-DD date — language-agnostic.
        # Matches English "## 2026-05-14T10:23 — Session: Update", Vietnamese
        # "## 2026-05-14T10:23 — Phiên: Cập nhật", or any translated form.
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
            # Try to extract a "Mode:" line from the last session block.
            block = text[last.end():]
            next_heading = re.search(r"^##\s", block, re.MULTILINE)
            block_end = next_heading.start() if next_heading else len(block)
            mode_match = re.search(r"^[-*]\s*\*\*Mode:\*\*\s*([^\n—-]+)", block[:block_end], re.MULTILINE)
            if mode_match:
                state["mode_from_prior_session"] = mode_match.group(1).strip()

    # Derive a recommended resume intent + fresh_reason discriminator so
    # the headless audit trail does not collapse "no prior workspace" with
    # "prior workspace exists but stepsCompleted is empty (crashed)".
    steps = state["primary_steps_completed"]
    state["fresh_reason"] = None
    if not state["primary_exists"]:
        state["recommended_intent"] = "Fresh"
        state["fresh_reason"] = "no_workspace"
    elif not steps:
        state["recommended_intent"] = "Fresh"
        state["fresh_reason"] = "crashed_no_progress"
    elif "stage-5" in steps:
        state["recommended_intent"] = "Update"
    elif "stage-1" in steps:
        state["recommended_intent"] = "Resume"
    else:
        state["recommended_intent"] = "Fresh"
        state["fresh_reason"] = "stale_artifact"  # frontmatter exists but no stage-1 yet

    return state


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("planning_artifacts", help="Path to planning_artifacts directory")
    parser.add_argument(
        "--template-path",
        required=True,
        help="Resolved path to business_flow_template (Stage 1 will refuse to start if missing)",
    )
    parser.add_argument(
        "--workspace",
        default=None,
        help="Optional: path to {doc_workspace}. When provided, the script emits resume_state for Stage 1a.",
    )
    parser.add_argument(
        "--check-as-is",
        action="store_true",
        help="Scan PRD files for AS-IS / 現状 / 'current state' markers. Returns as_is object in output.",
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
        "ux": [],
        "use_case": [],
        "research": [],
    }

    fatal = False

    if not template.exists():
        result["fatal"] = "template_missing"
        fatal = True

    if not artifacts.exists():
        result["artifacts_status"] = "directory_missing"
    else:
        prd_files = _glob(artifacts, PRD_GLOBS)
        # Word-boundary match for PRD directory names: matches "prd/" and
        # "prd-customer/" but not "approved/" or "notes-on-the-prd/".
        prd_name_re = re.compile(r"\bprd\b", re.IGNORECASE)
        prd_dirs = [
            d
            for d in artifacts.iterdir()
            if d.is_dir() and prd_name_re.search(d.name) and (d / "index.md").exists()
        ]
        result["prd"] = [_classify_prd(p) for p in _unique_paths(prd_files + prd_dirs)]
        result["ux"] = [_make_entry(p) for p in _glob(artifacts, UX_GLOBS)]
        result["use_case"] = [_make_entry(p) for p in _glob(artifacts, USE_CASE_GLOBS)]
        result["research"] = [_make_entry(p) for p in _glob(artifacts, RESEARCH_GLOBS)]

    if args.check_as_is and result["prd"]:
        result["as_is"] = _check_as_is(result["prd"])

    if args.workspace:
        result["resume_state"] = _extract_resume_state(Path(args.workspace))

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": args.output, "fatal": result.get("fatal", None)}))
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
