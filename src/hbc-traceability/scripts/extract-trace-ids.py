#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Extract IDs matching a regex pattern from one or more files.

Scans files matching a glob pattern for occurrences of a regex,
returns deduplicated IDs as JSON. Used by hbc-traceability to extract
REQ-xxx, TC-xxx, entity names, etc. from project artifacts.
"""

import argparse
import glob
import json
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path


def extract_ids(source_pattern: str, regex: str, project_root: str) -> dict:
    """Extract unique IDs from files matching the source pattern."""
    if not Path(source_pattern).is_absolute():
        source_pattern = str(Path(project_root) / source_pattern)

    matches = glob.glob(source_pattern, recursive=True)
    if not matches:
        return {
            "status": "NO_FILES",
            "pattern": source_pattern,
            "ids": [],
            "file_count": 0,
        }

    all_ids: list[str] = []
    files_scanned: list[str] = []

    for fpath in sorted(matches):
        try:
            content = Path(fpath).read_text(encoding="utf-8")
            found = re.findall(regex, content)
            if found:
                all_ids.extend(found)
                files_scanned.append(Path(fpath).name)
        except (OSError, UnicodeDecodeError):
            continue

    unique_ids = list(dict.fromkeys(all_ids))

    return {
        "status": "OK" if unique_ids else "NO_MATCHES",
        "pattern": source_pattern,
        "regex": regex,
        "ids": unique_ids,
        "total_found": len(all_ids),
        "unique_count": len(unique_ids),
        "file_count": len(files_scanned),
        "files_scanned": files_scanned,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract IDs matching a regex from project artifacts."
    )
    parser.add_argument(
        "--source", required=True, help="Glob pattern for source files"
    )
    parser.add_argument(
        "--pattern", required=True, help="Regex pattern to match IDs"
    )
    parser.add_argument(
        "--project-root", required=True, help="Project root directory"
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    result = extract_ids(args.source, args.pattern, args.project_root)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0 if result["status"] == "OK" else 1)


if __name__ == "__main__":
    main()
