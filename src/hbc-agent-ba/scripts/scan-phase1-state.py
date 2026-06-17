#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan Phase 1 artifacts and return structured JSON status."""

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
    "D-02": "D-02*",
    "D-03": "D-03*",
    "D-06": "D-06*",
    "phase-1-gate": "phase-1-gate*",
}

CORE_ARTIFACTS = {"D-02", "D-03", "D-06"}

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


def _resolve_dir(key: str, output_path: str, gates_dir: str | None, shared_glossary_dir: str | None) -> str:
    """Route each Phase-1 deliverable to its correct scope.

    - gate report  -> gates_dir (per-feature gates) when provided
    - D-03 glossary -> shared_glossary_dir (SHARED) when provided
    - D-02/D-06     -> output_path (per-feature planning-artifacts)
    """
    if "gate" in key and gates_dir and os.path.isdir(gates_dir):
        return gates_dir
    if key == "D-03" and shared_glossary_dir and os.path.isdir(shared_glossary_dir):
        return shared_glossary_dir
    return output_path


def scan(
    output_path: str,
    gates_dir: str | None = None,
    shared_glossary_dir: str | None = None,
) -> dict:
    phase1_state = {}

    for key, pattern in ARTIFACT_PATTERNS.items():
        search_dir = _resolve_dir(key, output_path, gates_dir, shared_glossary_dir)
        matches = glob.glob(os.path.join(search_dir, pattern))
        if matches:
            filepath = matches[0]
            phase1_state[key] = {
                "exists": True,
                "file": os.path.basename(filepath),
                "path": filepath,
                "updated": read_frontmatter_date(filepath),
            }
        else:
            phase1_state[key] = {"exists": False, "file": None, "path": None, "updated": None}

    core_complete = all(
        phase1_state.get(k, {}).get("exists", False) for k in CORE_ARTIFACTS
    )

    if core_complete:
        status = "complete"
        next_recommended = "PG"
        reason = "All core artifacts exist — recommend running Phase 1 gate"
    else:
        missing = [k for k in ["D-02", "D-03", "D-06"] if not phase1_state[k]["exists"]]
        status = "blocked"
        next_recommended = missing[0] if missing else "PG"
        label = {"D-02": "Requirements", "D-03": "Glossary", "D-06": "Business Flow"}
        reason = f"{', '.join(missing)} missing — next: {label.get(missing[0], missing[0])}"

    return {
        "status": status,
        "phase1_state": phase1_state,
        "next_recommended": next_recommended,
        "reason": reason,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan Phase 1 artifact state")
    parser.add_argument(
        "output_path",
        help="Per-feature planning-artifacts dir (D-02/D-06 live here)",
    )
    parser.add_argument(
        "-o", "--output", help="Write JSON to file instead of stdout"
    )
    parser.add_argument("--gates-dir", help="Separate directory for gate reports (per-feature gates)")
    parser.add_argument(
        "--output-folder",
        help="HBC output folder (e.g. _bmad-output); used to resolve SHARED D-03 under {output-folder}/shared/glossary",
    )
    parser.add_argument(
        "--feature",
        help="Feature slug (accepted for symmetry; per-feature deliverables are passed via output_path)",
    )
    args = parser.parse_args()

    # D-03 glossary is SHARED, not per-feature: resolve it under
    # {output-folder}/shared/glossary so it isn't reported missing.
    shared_glossary_dir = (
        os.path.join(args.output_folder, "shared", "glossary")
        if args.output_folder
        else None
    )

    if not os.path.isdir(args.output_path):
        result = {
            "status": "blocked",
            "phase1_state": {
                k: {"exists": False, "file": None, "path": None, "updated": None}
                for k in ARTIFACT_PATTERNS
            },
            "next_recommended": "D-02",
            "reason": f"Output directory not found: {args.output_path}",
        }
    else:
        result = scan(
            args.output_path,
            gates_dir=args.gates_dir,
            shared_glossary_dir=shared_glossary_dir,
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
