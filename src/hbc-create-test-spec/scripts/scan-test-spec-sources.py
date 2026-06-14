#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan project for test-spec sources and detect D-27 state.

Returns a compact JSON manifest for Stage 1 Prerequisites:
resume state, discovered source documents (D-26 test plan,
D-02 requirements, D-19 ER diagram, D-06 business flow),
and REQ IDs extracted from D-02.
"""

import argparse
import json
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REQ_ID_RE = re.compile(r"REQ-\d{3,}")
TC_COUNT_RE = re.compile(r"tc_count:\s*['\"]?(\d+)['\"]?")


def parse_frontmatter(path: Path) -> dict:
    """Extract frontmatter fields from a markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    fields: dict = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip().strip('"').strip("'")
    return fields


def extract_req_ids(path: Path) -> list[str]:
    """Extract unique REQ-xxx IDs from a document, sorted."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    ids = sorted(set(REQ_ID_RE.findall(text)))
    return ids


def find_doc(search_dirs: list[Path], prefix: str) -> Path | None:
    """Find the first file matching the given prefix in search directories."""
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for path in sorted(search_dir.glob(f"{prefix}*")):
            if path.is_file():
                return path
    return None


def parse_tc_count(path: Path) -> str | None:
    """Extract tc_count from D-27 frontmatter."""
    fm = parse_frontmatter(path)
    if "tc_count" in fm:
        return fm["tc_count"]

    # Fallback: search for tc_count in the raw frontmatter block
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    match = TC_COUNT_RE.search(text)
    return match.group(1) if match else None


def scan_sources(project_root: str, output_dir: str | None = None) -> dict:
    """Scan project for test-spec sources and existing D-27."""
    root = Path(project_root)

    if output_dir:
        out_dir = Path(output_dir) if Path(output_dir).is_absolute() else root / output_dir
    else:
        out_dir = root / "_bmad-output" / "planning-artifacts"

    search_dirs: list[Path] = []
    if out_dir.exists():
        search_dirs.append(out_dir)
    # Also search the broader _bmad-output tree
    hbc_output = root / "_bmad-output"
    if hbc_output.exists():
        for sub in sorted(hbc_output.iterdir()):
            if sub.is_dir() and sub != out_dir:
                search_dirs.append(sub)
    search_dirs.append(root)

    # --- Detect existing D-27 ---
    existing_d27: dict | None = None
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for path in sorted(search_dir.glob("D-27*")):
            if path.is_file():
                fm = parse_frontmatter(path)
                existing_d27 = {
                    "path": str(path.relative_to(root)),
                    "lastStep": fm.get("lastStep", ""),
                    "version": fm.get("version", ""),
                    "tc_count": parse_tc_count(path),
                }
                break
        if existing_d27:
            break

    # --- Determine state ---
    state = "fresh"
    if existing_d27:
        if existing_d27.get("lastStep") == "complete":
            state = "update"
        else:
            state = "resume"

    # --- Find source documents ---
    # D-26 test plan, D-02 requirements, D-19 ER diagram, D-06 business flow
    d26_path_obj = find_doc(search_dirs, "D-26")
    d02_path_obj = find_doc(search_dirs, "D-02")
    d19_path_obj = find_doc(search_dirs, "D-19")
    d06_path_obj = find_doc(search_dirs, "D-06")

    d26_path: str | None = str(d26_path_obj.relative_to(root)) if d26_path_obj else None
    d02_path: str | None = str(d02_path_obj.relative_to(root)) if d02_path_obj else None
    d19_path: str | None = str(d19_path_obj.relative_to(root)) if d19_path_obj else None
    d06_path: str | None = str(d06_path_obj.relative_to(root)) if d06_path_obj else None

    # --- Extract REQ IDs from D-02 ---
    req_ids: list[str] = []
    if d02_path_obj:
        req_ids = extract_req_ids(d02_path_obj)

    # --- Count discovered sources ---
    source_count = sum(
        1 for p in [d26_path, d02_path, d19_path, d06_path] if p is not None
    )

    return {
        "state": state,
        "existing_d27": existing_d27,
        "d26_path": d26_path,
        "d02_path": d02_path,
        "d19_path": d19_path,
        "d06_path": d06_path,
        "req_ids": req_ids,
        "source_count": source_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan project for test-spec sources and detect D-27 state."
    )
    parser.add_argument(
        "--project-root", required=True, help="Project root directory"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for D-27 (default: {project-root}/_bmad-output/planning-artifacts)",
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    result = scan_sources(args.project_root, output_dir=args.output_dir)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0)


if __name__ == "__main__":
    main()
