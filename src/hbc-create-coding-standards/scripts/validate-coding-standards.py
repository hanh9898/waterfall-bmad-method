#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-12 Coding Standards document.

Checks required sections are present and non-empty,
detects internal contradictions, verifies framework-specific
conventions, and returns structured JSON with per-issue auto_fixable flag.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("概要", "Overview"),
    ("命名規約", "Naming Conventions"),
    ("フォーマット", "Formatting"),
    ("コメント", "Comments"),
    ("インポート", "Imports"),
    ("エラーハンドリング", "Error Handling"),
    ("セキュリティ", "Security"),
    ("テスト", "Testing"),
    ("フレームワーク固有", "Framework-Specific"),
    ("Git規約", "Git Conventions"),
]

CONTRADICTION_PAIRS = [
    (r"\btabs?\b", r"\bspaces?\b", "indentation"),
    (r"single[- ]?quotes?", r"double[- ]?quotes?", "quote style"),
    (r"semicolons?\s+required", r"no\s+semicolons?", "semicolons"),
]

FRAMEWORK_CONVENTIONS: dict[str, list[str]] = {
    "odoo": ["@api", "_inherit", "ir.model", "xml", "odoo"],
    "django": ["pep 8", "class-based view", "model", "migration", "django"],
    "nextjs": ["eslint", "component", "hook", "server component", "next"],
    "react": ["eslint", "component", "hook", "jsx", "react"],
    "laravel": ["psr", "eloquent", "blade", "artisan", "laravel"],
    "spring": ["@RestController", "bean", "spring", "maven", "gradle"],
    "flask": ["pep 8", "blueprint", "flask", "jinja"],
    "fastapi": ["pep 8", "pydantic", "fastapi", "async"],
    "vue": ["eslint", "component", "composition api", "vue"],
    "angular": ["tslint", "eslint", "module", "component", "angular"],
}


def _section_has_content(text: str) -> bool:
    non_blank = [ln.strip() for ln in text.splitlines() if ln.strip()]

    skip: set[int] = set()
    for i, line in enumerate(non_blank):
        if i + 1 < len(non_blank):
            nxt = non_blank[i + 1]
            is_separator = nxt.startswith("|") and set(nxt) <= {"|", "-", " ", ":"}
            is_header = line.startswith("|") and not set(line) <= {"|", "-", " ", ":"}
            if is_header and is_separator:
                skip.add(i)
                skip.add(i + 1)

    for i, line in enumerate(non_blank):
        if i in skip:
            continue
        if set(line) <= {"|", "-", " ", ":"}:
            continue
        if line.startswith("<!--") and line.endswith("-->"):
            continue
        return True

    return False


def check_sections(content: str) -> list[dict]:
    issues: list[dict] = []

    for ja_name, en_name in REQUIRED_SECTIONS:
        pattern_ja = re.compile(rf"#+\s.*{re.escape(ja_name)}.*", re.IGNORECASE)
        pattern_en = re.compile(rf"#+\s.*{re.escape(en_name)}.*", re.IGNORECASE)
        match = pattern_ja.search(content) or pattern_en.search(content)
        if not match:
            issues.append({
                "type": "SECTION_MISSING",
                "message": f"Required section '{ja_name}' / '{en_name}' not found",
                "section": ja_name,
                "auto_fixable": False,
            })
            continue

        heading_level = len(match.group().split()[0])
        start = match.end()
        same_level_pattern = re.compile(r"\n#{1," + str(heading_level) + r"}\s")
        next_heading = same_level_pattern.search(content[start:])
        section_body = (
            content[start : start + next_heading.start()]
            if next_heading
            else content[start:]
        )

        stripped = re.sub(r"<!--.*?-->", "", section_body, flags=re.DOTALL)
        if not _section_has_content(stripped):
            issues.append({
                "type": "SECTION_EMPTY",
                "message": f"Section '{ja_name}' exists but has no content",
                "section": ja_name,
                "auto_fixable": False,
            })

    return issues


def check_contradictions(content: str) -> list[dict]:
    issues: list[dict] = []
    lower = content.lower()

    for pattern_a, pattern_b, topic in CONTRADICTION_PAIRS:
        has_a = re.search(pattern_a, lower)
        has_b = re.search(pattern_b, lower)
        if has_a and has_b:
            issues.append({
                "type": "CONTRADICTION",
                "message": f"Potential contradiction in {topic}: both '{has_a.group()}' and '{has_b.group()}' mentioned — verify intent",
                "topic": topic,
                "auto_fixable": False,
            })

    return issues


def check_framework_conventions(
    content: str, framework: str | None
) -> list[dict]:
    issues: list[dict] = []

    if not framework:
        return issues

    keywords = FRAMEWORK_CONVENTIONS.get(framework.lower(), [])
    if not keywords:
        return issues

    lower = content.lower()
    found = [kw for kw in keywords if kw.lower() in lower]

    if len(found) < 2:
        issues.append({
            "type": "FRAMEWORK_COVERAGE",
            "message": (
                f"Framework '{framework}' detected but only {len(found)} "
                f"framework-specific terms found (expected ≥2). "
                f"Section 9 (Framework-Specific) may need more detail."
            ),
            "framework": framework,
            "found_terms": found,
            "auto_fixable": False,
        })

    return issues


def check_code_examples(content: str) -> list[dict]:
    issues: list[dict] = []

    code_blocks = re.findall(r"```[\w]*\n.*?```", content, re.DOTALL)
    if len(code_blocks) < 3:
        issues.append({
            "type": "FEW_EXAMPLES",
            "message": (
                f"Only {len(code_blocks)} code examples found. "
                f"Coding standards should include concrete examples "
                f"for naming, formatting, and error handling at minimum."
            ),
            "count": len(code_blocks),
            "auto_fixable": False,
        })

    return issues


def validate(doc_path: str, framework: str | None = None) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    all_issues: list[dict] = []
    all_issues.extend(check_sections(content))
    all_issues.extend(check_contradictions(content))
    all_issues.extend(check_framework_conventions(content, framework))
    all_issues.extend(check_code_examples(content))

    auto_fixable = [i for i in all_issues if i.get("auto_fixable")]
    manual_fix = [i for i in all_issues if not i.get("auto_fixable")]

    section_count = len(
        re.findall(r"^##\s", content, re.MULTILINE)
    )

    return {
        "valid": len(all_issues) == 0,
        "total_issues": len(all_issues),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "section_count": section_count,
        "issues": all_issues,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate D-12 Coding Standards."
    )
    parser.add_argument("document", help="Path to D-12 coding standards document")
    parser.add_argument(
        "--framework", help="Expected framework (for convention checks)"
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        error = {
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-create-coding-standards' first to generate D-12.",
        }
        print(json.dumps(error, indent=2, ensure_ascii=False))
        sys.exit(1)

    result = validate(str(doc_path), args.framework)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
