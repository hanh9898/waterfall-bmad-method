#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan Phase 4 testing artifacts and return structured JSON status."""

import argparse
import glob
import json
import os
import re
import sys

ARTIFACT_PATTERNS = {
    "test-execution-report": "test-execution-report*",
    "acceptance-report": "acceptance-report*",
    "phase-4-gate": "phase-4-gate*",
}

CORE_ARTIFACTS = {"test-execution-report", "acceptance-report"}

FRONTMATTER_DATE_RE = re.compile(
    r"^(?:last_touched|updated|executed_at|decided_at)\s*:\s*(.+)$", re.MULTILINE
)

DECISION_RE = re.compile(
    r"(?:decision|status)\s*:\s*[\"']?(ACCEPTED|REJECTED|DEFERRED|PENDING)[\"']?",
    re.IGNORECASE,
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
    return match.group(1).strip().strip("'\"") if match else None


def read_acceptance_decision(filepath: str) -> str | None:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(4096)
    except (OSError, UnicodeDecodeError):
        return None

    match = DECISION_RE.search(content)
    return match.group(1).upper() if match else None


def scan(output_path: str, gates_dir: str | None = None) -> dict:
    testing_state: dict = {}

    for key, pattern in ARTIFACT_PATTERNS.items():
        search_dir = gates_dir if ("gate" in key and gates_dir and os.path.isdir(gates_dir)) else output_path
        matches = glob.glob(os.path.join(search_dir, pattern))
        if matches:
            filepath = matches[0]
            testing_state[key] = {
                "exists": True,
                "file": os.path.basename(filepath),
                "path": filepath,
                "updated": read_frontmatter_date(filepath),
            }
        else:
            testing_state[key] = {
                "exists": False,
                "file": None,
                "path": None,
                "updated": None,
            }

    te_exists = testing_state["test-execution-report"]["exists"]
    ac_exists = testing_state["acceptance-report"]["exists"]

    acceptance_decision = None
    if ac_exists:
        acceptance_decision = read_acceptance_decision(
            testing_state["acceptance-report"]["path"]
        )

    core_complete = te_exists and ac_exists and acceptance_decision == "ACCEPTED"

    if core_complete:
        status = "complete"
        next_recommended = "PG"
        reason = "Testing complete, ACCEPTED — recommend running final Phase 4 gate"
    elif not te_exists:
        status = "blocked"
        next_recommended = "TE"
        reason = "Test execution report missing — run tests first"
    elif not ac_exists:
        status = "blocked"
        next_recommended = "AC"
        reason = "Test execution done — next: Acceptance Check"
    else:
        status = "blocked"
        next_recommended = "AC"
        reason = f"Acceptance decision: {acceptance_decision or 'unknown'} — review needed"

    return {
        "status": status,
        "testing_state": testing_state,
        "acceptance_decision": acceptance_decision,
        "next_recommended": next_recommended,
        "reason": reason,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan Phase 4 testing artifact state")
    parser.add_argument("output_path", help="Path to scan for testing artifacts")
    parser.add_argument(
        "-o", "--output", help="Write JSON to file instead of stdout"
    )
    parser.add_argument("--gates-dir", help="Separate directory for gate reports")
    args = parser.parse_args()

    if not os.path.isdir(args.output_path):
        result = {
            "status": "blocked",
            "testing_state": {
                k: {"exists": False, "file": None, "path": None, "updated": None}
                for k in ARTIFACT_PATTERNS
            },
            "acceptance_decision": None,
            "next_recommended": "TE",
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
