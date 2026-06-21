#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-17 Behavioral Design document (structure only).

Checks required sections (English canonical + configured document language — NO
hardcoded Japanese), at least one behavioural element with a well-formed id
(ST-/DR-/INV-/SEQ-NN), element-id uniqueness, and at least one REQ reference.
Semantic adequacy (do transitions cover illegal paths? are decision tables
complete? do referenced entities exist in D-19?) is the LLM review layer.
"""

import argparse
import json
import re
import sys
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        find_section,
        section_body,
        section_has_content,
        verdict,
    )
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

REQUIRED_SECTIONS = [
    ("Overview", "Tổng quan"),
    ("Revision History", "Lịch sử sửa đổi"),
]

REQ_RE = re.compile(r"\bREQ-(?:[A-Z0-9]+-)+\d{3,}\b")
# A DEFINITION is an element id in the first cell of a table row. Mentions in
# prose or in other columns are references and must not be counted (else a prose
# mention or a cross-reference would look like a duplicate definition).
ELEMENT_RE = re.compile(r"(?m)^\|\s*(ST|DR|INV|SEQ)-(\d+)\s*\|")


def check_sections(content: str) -> list[dict]:
    issues: list[dict] = []
    for en_name, lang_name in REQUIRED_SECTIONS:
        match = find_section(content, en_name, lang_name)
        if not match:
            issues.append({
                "type": "SECTION_MISSING",
                "message": f"Required section '{en_name}' / '{lang_name}' not found",
                "section": en_name, "auto_fixable": False,
            })
        elif not section_has_content(section_body(content, match)):
            issues.append({
                "type": "SECTION_EMPTY",
                "message": f"Section '{en_name}' is empty",
                "section": en_name, "auto_fixable": False,
            })
    return issues


def check_elements(content: str) -> tuple[list[dict], int]:
    ids = [f"{m.group(1)}-{m.group(2)}" for m in ELEMENT_RE.finditer(content)]
    issues: list[dict] = []
    if not ids:
        issues.append({
            "type": "NO_BEHAVIOR_ELEMENT",
            "message": "No behavioural element found (expected ST-/DR-/INV-/SEQ-NN)",
            "auto_fixable": False,
        })
    dups = [eid for eid, n in Counter(ids).items() if n > 1]
    for d in dups:
        issues.append({
            "type": "DUPLICATE_ELEMENT_ID",
            "message": f"Duplicate element id: '{d}'",
            "element": d, "auto_fixable": False,
        })
    return issues, len(set(ids))


def check_req_refs(content: str) -> list[dict]:
    if not REQ_RE.search(content):
        return [{
            "type": "NO_REQ_REF",
            "message": "No REQ-<FEAT>-NNN reference — each behaviour section must name its requirement",
            "auto_fixable": False,
        }]
    return []


CHECKED = [
    "required sections present and non-empty",
    "at least one behavioural element (ST/DR/INV/SEQ) with well-formed id",
    "element-id uniqueness",
    "at least one REQ reference",
]
NOT_CHECKED = [
    "transitions cover illegal paths, not only happy (LLM review)",
    "decision tables complete / invariants enforceable (LLM review)",
    "referenced entities/fields exist in D-19 (LLM review / readiness gate)",
]


def validate(doc_path: str) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    issues: list[dict] = []
    issues.extend(check_sections(content))
    elem_issues, element_count = check_elements(content)
    issues.extend(elem_issues)
    issues.extend(check_req_refs(content))

    structure_ok = len(issues) == 0
    result = verdict(structure_ok, semantic_review=SEMANTIC_NA, checked=CHECKED, not_checked=NOT_CHECKED)
    result.update({
        "valid": structure_ok,
        "total_issues": len(issues),
        "auto_fixable_count": len([i for i in issues if i.get("auto_fixable")]),
        "manual_fix_count": len([i for i in issues if not i.get("auto_fixable")]),
        "element_count": element_count,
        "issues": issues,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate D-17 Behavioral Design document.")
    parser.add_argument("document", help="Path to D-17 document")
    parser.add_argument("--project-root", required=True, help="Project root directory")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(json.dumps({
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-create-behavioral-design' first to generate D-17.",
        }, indent=2, ensure_ascii=False))
        sys.exit(1)

    result = validate(str(doc_path))
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(text)
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
