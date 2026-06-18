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

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

# --- shared lib bootstrap (Phase 0 / C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import SEMANTIC_NA, check_required_sections, verdict  # noqa: E402
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install the hbc-shared component alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

# (English canonical, configured-language label). English reported in issues;
# either label satisfies presence. No hardcoded Japanese.
REQUIRED_SECTIONS = [
    ("Overview", "Tổng quan"),
    ("Naming Conventions", "Quy ước đặt tên"),
    ("Formatting", "Định dạng"),
    ("Comments", "Chú thích"),
    ("Imports", "Import"),
    ("Error Handling", "Xử lý lỗi"),
    ("Security", "Bảo mật"),
    ("Testing", "Kiểm thử"),
    ("Framework-Specific", "Đặc thù framework"),
    ("Git Conventions", "Quy ước Git"),
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


def check_sections(content: str) -> list[dict]:
    """Required sections present + non-empty (shared lib; English or VN label)."""
    return check_required_sections(content, REQUIRED_SECTIONS)


def check_contradictions(content: str) -> list[dict]:
    """ADVISORY only. Mentioning both sides of a choice (e.g. "use spaces, never
    tabs") is normal — even mandatory — in a standards document, so this can NOT
    decide a real contradiction; it merely flags a pair for the reviewer to eyeball.
    Marked advisory so it never fails the structural verdict (a blocking version
    false-failed virtually every valid D-12, whose indentation rule names both)."""
    issues: list[dict] = []
    lower = content.lower()

    for pattern_a, pattern_b, topic in CONTRADICTION_PAIRS:
        has_a = re.search(pattern_a, lower)
        has_b = re.search(pattern_b, lower)
        if has_a and has_b:
            issues.append({
                "type": "CONTRADICTION",
                "message": f"Both '{has_a.group()}' and '{has_b.group()}' mentioned for {topic} — likely a 'use X not Y' rule; verify it is not a real conflict",
                "topic": topic,
                "auto_fixable": False,
                "advisory": True,
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

    # Advisory issues (e.g. heuristic contradictions) are surfaced but do NOT fail
    # the structural verdict.
    blocking = [i for i in all_issues if not i.get("advisory")]
    structure_ok = len(blocking) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=["required sections present/non-empty", "contradictions", "framework coverage", "code examples"],
        not_checked=["standard correctness / quality (LLM review)", "fit with actual codebase (LLM review)"],
    )
    result.update({
        "valid": structure_ok,
        "total_issues": len(all_issues),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "section_count": section_count,
        "issues": all_issues,
    })
    return result


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
