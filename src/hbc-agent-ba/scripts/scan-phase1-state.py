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


def scan(output_path: str) -> dict:
    phase1_state = {}

    for key, pattern in ARTIFACT_PATTERNS.items():
        matches = glob.glob(os.path.join(output_path, pattern))
        if matches:
            filepath = matches[0]
            phase1_state[key] = {
                "exists": True,
                "file": os.path.basename(filepath),
                "updated": read_frontmatter_date(filepath),
            }
        else:
            phase1_state[key] = {"exists": False, "file": None, "updated": None}

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
    parser.add_argument("output_path", help="Path to scan for Phase 1 artifacts")
    parser.add_argument(
        "-o", "--output", help="Write JSON to file instead of stdout"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.output_path):
        result = {
            "status": "blocked",
            "phase1_state": {
                k: {"exists": False, "file": None, "updated": None}
                for k in ARTIFACT_PATTERNS
            },
            "next_recommended": "D-02",
            "reason": f"Output directory not found: {args.output_path}",
        }
    else:
        result = scan(args.output_path)

    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)

    sys.exit(0 if result["status"] == "complete" else 1)


if __name__ == "__main__":
    main()
