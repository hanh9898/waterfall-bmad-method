#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Scan project for test plan sources and detect project state.

Returns a compact JSON manifest for Stage 1 Prerequisites:
resume state, discovered source documents, detected test framework,
and project-context path.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Mapping of framework indicator files/keys to framework names.
PACKAGE_JSON_FRAMEWORKS: list[tuple[str, str]] = [
    ("vitest", "vitest"),
    ("jest", "jest"),
    ("mocha", "mocha"),
    ("jasmine", "jasmine"),
    ("cypress", "cypress"),
    ("playwright", "playwright"),
    ("ava", "ava"),
    ("tap", "tap"),
]

CARGO_TOML_RE = re.compile(r"^\[(?:dev-)?dependencies\]", re.MULTILINE)
GO_MOD_FRAMEWORKS: list[tuple[str, str]] = [
    ("github.com/stretchr/testify", "testify"),
    ("gotest.tools", "gotest"),
]


def parse_frontmatter(path: Path) -> dict[str, str]:
    """Extract frontmatter fields from a markdown file."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}

    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}

    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fields[key.strip()] = val.strip().strip('"').strip("'")
    return fields


def find_existing_d26(root: Path, output_dir: Path) -> dict[str, str] | None:
    """Search for existing D-26 test plan documents."""
    search_dirs: list[Path] = []
    if output_dir.exists():
        search_dirs.append(output_dir)
    if root not in search_dirs:
        search_dirs.append(root)

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for path in search_dir.glob("D-26*"):
            if path.is_file():
                fm = parse_frontmatter(path)
                return {
                    "path": str(path.relative_to(root)),
                    "lastStep": fm.get("lastStep", ""),
                    "version": fm.get("version", ""),
                }
    return None


def find_source_doc(root: Path, output_dir: Path, prefix: str) -> str | None:
    """Find a source document by prefix (e.g. 'D-02', 'D-06')."""
    search_dirs: list[Path] = []
    if output_dir.exists():
        search_dirs.append(output_dir)
    if root not in search_dirs:
        search_dirs.append(root)

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for path in search_dir.glob(f"{prefix}*"):
            if path.is_file():
                return str(path.relative_to(root))
    return None


def find_project_context(root: Path) -> str | None:
    """Find project-context.md anywhere in the project."""
    for ctx in root.rglob("project-context.md"):
        return str(ctx.relative_to(root))
    return None


def detect_framework(root: Path) -> str | None:
    """Detect test framework from project configuration files."""
    # Check package.json (Node.js / JS / TS)
    pkg_json = root / "package.json"
    if pkg_json.is_file():
        try:
            text = pkg_json.read_text(encoding="utf-8")
            data = json.loads(text)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            data = {}

        all_deps = {}
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            if isinstance(data.get(key), dict):
                all_deps.update(data[key])

        # Also check scripts for framework references
        scripts_text = json.dumps(data.get("scripts", {}))

        for indicator, framework in PACKAGE_JSON_FRAMEWORKS:
            if indicator in all_deps or indicator in scripts_text:
                return framework

    # Check requirements.txt / setup.cfg / pyproject.toml (Python)
    for pyfile in ("requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.cfg"):
        path = root / pyfile
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "pytest" in text:
                return "pytest"
            if "unittest" in text:
                return "unittest"
            if "nose" in text:
                return "nose"

    # Check go.mod (Go)
    go_mod = root / "go.mod"
    if go_mod.is_file():
        try:
            text = go_mod.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = ""
        for indicator, framework in GO_MOD_FRAMEWORKS:
            if indicator in text:
                return framework
        # Go has built-in testing
        if text:
            return "go-test"

    # Check Cargo.toml (Rust)
    cargo_toml = root / "Cargo.toml"
    if cargo_toml.is_file():
        return "cargo-test"

    # Check build.gradle / build.gradle.kts (JVM)
    for gradle in ("build.gradle", "build.gradle.kts"):
        path = root / gradle
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if "junit" in text.lower() or "kotest" in text.lower():
                return "junit"

    return None


def determine_state(existing_d26: dict[str, str] | None) -> str:
    """Determine workflow state from existing D-26 document."""
    if existing_d26 is None:
        return "fresh"
    if existing_d26.get("lastStep") == "complete":
        return "update"
    return "resume"


def scan_sources(project_root: str, output_dir: str | None = None) -> dict:
    """Scan project for test plan sources and existing D-26."""
    root = Path(project_root)
    out_dir = Path(output_dir) if output_dir else root / "_bmad-output" / "planning-artifacts"

    existing_d26 = find_existing_d26(root, out_dir)
    state = determine_state(existing_d26)

    d02_path = find_source_doc(root, out_dir, "D-02")
    d06_path = find_source_doc(root, out_dir, "D-06")
    project_context_path = find_project_context(root)
    framework = detect_framework(root)

    source_count = sum(1 for p in (d02_path, d06_path, project_context_path) if p is not None)

    return {
        "state": state,
        "existing_d26": existing_d26,
        "d02_path": d02_path,
        "d06_path": d06_path,
        "framework": framework,
        "project_context_path": project_context_path,
        "source_count": source_count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan project for test plan sources and detect project state."
    )
    parser.add_argument(
        "--project-root", required=True, help="Project root directory"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for D-26 (default: {project-root}/_bmad-output/planning-artifacts)",
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
