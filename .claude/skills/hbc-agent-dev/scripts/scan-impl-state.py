#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan implementation artifacts and return structured JSON status."""

import argparse
import glob
import json
import os
import re
import sys

TASK_BREAKDOWN_PATTERN = "task-breakdown*"

FRONTMATTER_DATE_RE = re.compile(
    r"^(?:last_touched|updated)\s*:\s*(.+)$", re.MULTILINE
)

# Markdown checkbox patterns:
#   - [x] or - [X] => DONE
#   - [ ] with "IN_PROGRESS" or "🔄" marker => IN_PROGRESS
#   - [ ] otherwise => TODO
CHECKBOX_DONE_RE = re.compile(r"^[\s]*-\s*\[x\]", re.IGNORECASE | re.MULTILINE)
CHECKBOX_UNCHECKED_RE = re.compile(r"^[\s]*-\s*\[\s\](.*)$", re.MULTILINE)
IN_PROGRESS_MARKER_RE = re.compile(r"IN[_\s]?PROGRESS|🔄", re.IGNORECASE)

COVERAGE_PATTERNS = [
    "coverage.xml",
    "coverage.json",
    "htmlcov/index.html",
    "coverage-report*",
    ".coverage",
    "test-results*",
    "junit*.xml",
]


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


def count_tasks(content: str) -> dict[str, int]:
    done = len(CHECKBOX_DONE_RE.findall(content))

    unchecked_matches = CHECKBOX_UNCHECKED_RE.findall(content)
    in_progress = 0
    todo = 0
    for line_rest in unchecked_matches:
        if IN_PROGRESS_MARKER_RE.search(line_rest):
            in_progress += 1
        else:
            todo += 1

    return {"done": done, "in_progress": in_progress, "todo": todo}


def find_coverage(output_path: str) -> float | None:
    project_root = os.path.dirname(output_path.rstrip(os.sep))
    search_dirs = [output_path, project_root]

    for search_dir in search_dirs:
        for pattern in COVERAGE_PATTERNS:
            matches = glob.glob(os.path.join(search_dir, pattern))
            if not matches:
                matches = glob.glob(os.path.join(search_dir, "**", pattern), recursive=True)
            if matches:
                # Try to extract coverage percentage from coverage.json
                for m in matches:
                    if m.endswith(".json"):
                        try:
                            with open(m, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            if "totals" in data and "percent_covered" in data["totals"]:
                                return float(data["totals"]["percent_covered"])
                        except (OSError, json.JSONDecodeError, KeyError, TypeError):
                            pass
                return None  # File found but could not extract percentage
    return None


def find_next_task(content: str) -> str | None:
    """Find the first TODO or IN_PROGRESS task ID (e.g., TASK-011)."""
    task_id_re = re.compile(r"TASK-\d+")
    for line in content.splitlines():
        unchecked = CHECKBOX_UNCHECKED_RE.match(line)
        if unchecked:
            match = task_id_re.search(line)
            if match:
                return match.group(0)
    return None


def scan(output_path: str) -> dict:
    tb_matches = glob.glob(os.path.join(output_path, TASK_BREAKDOWN_PATTERN))

    if tb_matches:
        filepath = tb_matches[0]
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            content = ""

        counts = count_tasks(content)
        task_info = {
            "exists": True,
            "file": os.path.basename(filepath),
            "path": filepath,
            "updated": read_frontmatter_date(filepath),
        }
        total = counts["done"] + counts["in_progress"] + counts["todo"]
        next_task = find_next_task(content)
    else:
        counts = {"done": 0, "in_progress": 0, "todo": 0}
        task_info = {"exists": False, "file": None, "path": None, "updated": None}
        total = 0
        next_task = None

    coverage = find_coverage(output_path)
    remaining = counts["in_progress"] + counts["todo"]
    all_done = task_info["exists"] and total > 0 and remaining == 0

    if all_done:
        status = "complete"
        next_recommended = "PG"
        reason = f"All {total} tasks done — recommend running Phase 3 gate"
    elif not task_info["exists"] or total == 0:
        status = "blocked"
        next_recommended = "TB"
        reason = "No task breakdown found — create one first" if not task_info["exists"] else "Task breakdown has no tasks — populate it first"
    else:
        status = "blocked"
        next_recommended = "IM"
        task_label = f"Implement {next_task}" if next_task else "Continue implementation"
        reason = f"{remaining} tasks remaining — next: {task_label}"

    return {
        "status": status,
        "impl_state": {
            "task_breakdown": task_info,
            "total_tasks": total,
            "done": counts["done"],
            "in_progress": counts["in_progress"],
            "todo": counts["todo"],
            "coverage": coverage,
        },
        "next_recommended": next_recommended,
        "reason": reason,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan implementation artifact state")
    parser.add_argument("output_path", help="Path to scan for implementation artifacts")
    parser.add_argument(
        "-o", "--output", help="Write JSON to file instead of stdout"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.output_path):
        result = {
            "status": "blocked",
            "impl_state": {
                "task_breakdown": {"exists": False, "file": None, "path": None, "updated": None},
                "total_tasks": 0,
                "done": 0,
                "in_progress": 0,
                "todo": 0,
                "coverage": None,
            },
            "next_recommended": "TB",
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

    sys.exit(0)


if __name__ == "__main__":
    main()
