#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan test design artifacts and return structured JSON status."""

import argparse
import glob
import json
import os
import re
import sys

ARTIFACT_PATTERNS = {
    "D-26": "D-26*",
    "D-27": "D-27*",
    "phase-2-gate": "phase-2-gate*",
}

CORE_ARTIFACTS = {"D-26", "D-27"}

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


def scan(output_path: str, gates_dir: str | None = None) -> dict:
    test_design_state = {}

    for key, pattern in ARTIFACT_PATTERNS.items():
        search_dir = gates_dir if ("gate" in key and gates_dir and os.path.isdir(gates_dir)) else output_path
        matches = glob.glob(os.path.join(search_dir, pattern))
        if matches:
            filepath = matches[0]
            test_design_state[key] = {
                "exists": True,
                "file": os.path.basename(filepath),
                "path": filepath,
                "updated": read_frontmatter_date(filepath),
            }
        else:
            test_design_state[key] = {"exists": False, "file": None, "path": None, "updated": None}

    core_complete = all(
        test_design_state.get(k, {}).get("exists", False) for k in CORE_ARTIFACTS
    )

    if core_complete:
        status = "complete"
        next_recommended = "PG"
        reason = "Test design artifacts exist — recommend running Phase 2 gate"
    else:
        missing = [k for k in ["D-26", "D-27"] if not test_design_state[k]["exists"]]
        status = "blocked"
        next_recommended = missing[0] if missing else "PG"
        label = {"D-26": "Test Plan", "D-27": "Test Specification"}
        reason = f"{', '.join(missing)} missing — next: {label.get(missing[0], missing[0])}"

    return {
        "status": status,
        "test_design_state": test_design_state,
        "next_recommended": next_recommended,
        "reason": reason,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan test design artifact state")
    parser.add_argument("output_path", help="Path to scan for test design artifacts")
    parser.add_argument(
        "-o", "--output", help="Write JSON to file instead of stdout"
    )
    parser.add_argument("--gates-dir", help="Separate directory for gate reports")
    args = parser.parse_args()

    if not os.path.isdir(args.output_path):
        result = {
            "status": "blocked",
            "test_design_state": {
                k: {"exists": False, "file": None, "path": None, "updated": None}
                for k in ARTIFACT_PATTERNS
            },
            "next_recommended": "D-26",
            "reason": f"Output directory not found: {args.output_path}",
        }
    else:
        result = scan(args.output_path, gates_dir=args.gates_dir)

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
