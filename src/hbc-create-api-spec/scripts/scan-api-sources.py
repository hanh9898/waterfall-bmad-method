#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan for existing D-21 API spec and prerequisite artifacts."""

import argparse
import glob
import json
import os
import re
import sys

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
FIELD_RE = re.compile(r"^(\w+)\s*:\s*(.+)$", re.MULTILINE)

NO_API_FRAMEWORKS = {"odoo"}

API_INDICATORS = [
    "api", "rest", "graphql", "endpoint", "swagger",
    "openapi", "postman", "curl", "http",
]


def read_frontmatter(filepath: str) -> dict[str, str]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(4096)
    except (OSError, UnicodeDecodeError):
        return {}

    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}

    fields = {}
    for m in FIELD_RE.finditer(match.group(1)):
        fields[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fields


def detect_framework(project_root: str) -> str | None:
    for pattern in [
        os.path.join(project_root, "project-context.md"),
        os.path.join(project_root, "_bmad", "project-context.md"),
        os.path.join(project_root, "**", "project-context.md"),
    ]:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            try:
                with open(matches[0], "r", encoding="utf-8") as f:
                    content = f.read().lower()
            except (OSError, UnicodeDecodeError):
                continue

            frameworks = {
                "odoo": ["odoo", "openerp", "_inherit"],
                "django": ["django", "manage.py"],
                "nextjs": ["next.js", "nextjs"],
                "react": ["react", "vite"],
                "laravel": ["laravel", "artisan"],
                "spring": ["spring boot", "spring"],
                "fastapi": ["fastapi", "uvicorn"],
            }
            scores = {}
            for fw, keywords in frameworks.items():
                score = sum(1 for kw in keywords if kw in content)
                if score > 0:
                    scores[fw] = score
            if scores:
                return max(scores, key=lambda k: scores[k])
    return None


def detect_needs_api(project_root: str, framework: str | None) -> bool | None:
    if framework and framework.lower() in NO_API_FRAMEWORKS:
        return False

    for pattern in [
        os.path.join(project_root, "**", "project-context.md"),
    ]:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            try:
                with open(matches[0], "r", encoding="utf-8") as f:
                    content = f.read().lower()
            except (OSError, UnicodeDecodeError):
                continue

            hits = sum(1 for ind in API_INDICATORS if ind in content)
            if hits >= 2:
                return True
            if hits == 0:
                return False

    return None


def find_artifact(output_dir: str, prefix: str) -> str | None:
    plan_dir = output_dir.replace("/design", "/plan")
    for search_dir in [output_dir, plan_dir]:
        matches = glob.glob(os.path.join(search_dir, f"{prefix}*"))
        if matches:
            return matches[0]
    return None


def scan(project_root: str, output_dir: str) -> dict:
    d21_matches = glob.glob(os.path.join(output_dir, "D-21*"))

    existing_d21 = None
    state = "fresh"

    if d21_matches:
        filepath = d21_matches[0]
        fm = read_frontmatter(filepath)
        last_step = fm.get("lastStep", "")

        if last_step == "complete":
            state = "update"
        elif last_step:
            state = "resume"
        else:
            state = "resume"

        existing_d21 = {
            "path": filepath,
            "file": os.path.basename(filepath),
            "frontmatter": fm,
        }

    framework = detect_framework(project_root)
    needs_api = detect_needs_api(project_root, framework)

    if not d21_matches and needs_api is False:
        state = "skip"

    d02_path = find_artifact(output_dir, "D-02")
    d19_path = find_artifact(output_dir, "D-19")

    return {
        "state": state,
        "existing_d21": existing_d21,
        "d02_path": d02_path,
        "d19_path": d19_path,
        "framework": framework,
        "needs_api": needs_api,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scan for existing D-21 and prerequisite artifacts."
    )
    parser.add_argument(
        "--project-root", required=True, help="Project root directory"
    )
    parser.add_argument(
        "--output-dir", required=True, help="Output directory to scan for D-21"
    )
    parser.add_argument("-o", "--output", help="Write JSON to file instead of stdout")
    args = parser.parse_args()

    result = scan(args.project_root, args.output_dir)

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
