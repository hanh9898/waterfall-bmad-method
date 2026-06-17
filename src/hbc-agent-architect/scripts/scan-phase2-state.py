#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan Phase 2 artifacts and return structured JSON status."""

import argparse
import glob
import json
import os
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ARTIFACT_PATTERNS = {
    "D-19": "D-19*",
    "D-12": "D-12*",
    "D-21": "D-21*",
    "phase-2-gate": "phase-2-gate*",
}

CORE_ARTIFACTS = {"D-19", "D-12"}

FRONTMATTER_DATE_RE = re.compile(
    r"^(?:last_touched|updated)\s*:\s*(.+)$", re.MULTILINE
)


def read_frontmatter_date(filepath: str) -> str | None:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(2048)
    except (OSError, UnicodeDecodeError):
        return None

    if not content.startswith("---"):
        return None

    end = content.find("---", 3)
    if end == -1:
        return None

    frontmatter = content[3:end]
    match = FRONTMATTER_DATE_RE.search(frontmatter)
    return match.group(1).strip() if match else None


def _candidate_dirs(
    key: str,
    output_path: str,
    gates_dir: str | None,
    shared_coding_dir: str | None,
    shared_erd_dir: str | None,
    shared_api_dir: str | None,
) -> list[str]:
    """Ordered list of dirs to search for a deliverable, by scope.

    Scope routing (first existing match wins -> path-existence precedence):
      - phase-2-gate : per-feature gates_dir (D-26/D-27 design gate also lives here)
      - D-12         : SHARED coding-standards dir only
      - D-19 (ERD)   : DUAL -> per-feature output_path first, then shared baseline
      - D-21 (API)   : DUAL -> per-feature output_path first, then shared baseline
    Unknown keys fall back to output_path. None/missing shared dirs are skipped,
    so back-compat callers (output_path only) keep working.
    """
    if "gate" in key:
        return [gates_dir] if (gates_dir and os.path.isdir(gates_dir)) else [output_path]
    if key == "D-12":
        return [d for d in (shared_coding_dir, output_path) if d]
    if key == "D-19":
        return [d for d in (output_path, shared_erd_dir) if d]
    if key == "D-21":
        return [d for d in (output_path, shared_api_dir) if d]
    return [output_path]


def scan(
    output_path: str,
    gates_dir: str | None = None,
    shared_coding_dir: str | None = None,
    shared_erd_dir: str | None = None,
    shared_api_dir: str | None = None,
) -> dict:
    phase2_state = {}

    for key, pattern in ARTIFACT_PATTERNS.items():
        matches: list[str] = []
        for search_dir in _candidate_dirs(
            key, output_path, gates_dir, shared_coding_dir, shared_erd_dir, shared_api_dir
        ):
            if not search_dir or not os.path.isdir(search_dir):
                continue
            matches = glob.glob(os.path.join(search_dir, pattern))
            if matches:
                break  # path-existence precedence: first scope with a match wins
        if matches:
            filepath = matches[0]
            phase2_state[key] = {
                "exists": True,
                "file": os.path.basename(filepath),
                "path": filepath,
                "updated": read_frontmatter_date(filepath),
            }
        else:
            phase2_state[key] = {"exists": False, "file": None, "path": None, "updated": None}

    core_complete = all(
        phase2_state.get(k, {}).get("exists", False) for k in CORE_ARTIFACTS
    )

    if core_complete:
        status = "complete"
        next_recommended = "PG"
        reason = "Core design artifacts exist — recommend running Phase 2 gate"
    else:
        missing = [k for k in ["D-19", "D-12"] if not phase2_state[k]["exists"]]
        status = "blocked"
        next_recommended = missing[0] if missing else "PG"
        label = {"D-19": "Database Design", "D-12": "Coding Standards"}
        reason = f"{', '.join(missing)} missing — next: {label.get(missing[0], missing[0])}"

    return {
        "status": status,
        "phase2_state": phase2_state,
        "next_recommended": next_recommended,
        "reason": reason,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan Phase 2 artifact state")
    parser.add_argument(
        "output_path",
        help="Per-feature planning-artifacts dir (D-26/D-27 and per-feature D-19/D-21 overrides live here)",
    )
    parser.add_argument(
        "-o", "--output", help="Write JSON to file instead of stdout"
    )
    parser.add_argument("--gates-dir", help="Separate directory for gate reports (per-feature gates)")
    parser.add_argument(
        "--output-folder",
        help="HBC output folder (e.g. _bmad-output); resolves SHARED D-12 and baseline D-19/D-21",
    )
    parser.add_argument(
        "--feature",
        help="Feature slug (accepted for symmetry; per-feature deliverables are passed via output_path)",
    )
    args = parser.parse_args()

    # Shared / baseline scopes derived from --output-folder.
    #   D-12 coding-standards : SHARED only
    #   D-19 ERD / D-21 API   : DUAL -> per-feature override (output_path) wins,
    #                           else shared baseline below.
    if args.output_folder:
        shared_coding_dir = os.path.join(args.output_folder, "shared", "coding-standards")
        shared_erd_dir = os.path.join(args.output_folder, "shared", "erd")
        shared_api_dir = os.path.join(args.output_folder, "shared", "api")
    else:
        shared_coding_dir = shared_erd_dir = shared_api_dir = None

    # Shared deliverables (D-12, baseline D-19/D-21) may exist even when the
    # per-feature output_path does not yet — only short-circuit when there is no
    # shared scope to fall back on (preserves back-compat behavior).
    if not os.path.isdir(args.output_path) and not args.output_folder:
        result = {
            "status": "blocked",
            "phase2_state": {
                k: {"exists": False, "file": None, "path": None, "updated": None}
                for k in ARTIFACT_PATTERNS
            },
            "next_recommended": "D-19",
            "reason": f"Output directory not found: {args.output_path}",
        }
    else:
        result = scan(
            args.output_path,
            gates_dir=args.gates_dir,
            shared_coding_dir=shared_coding_dir,
            shared_erd_dir=shared_erd_dir,
            shared_api_dir=shared_api_dir,
        )

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
