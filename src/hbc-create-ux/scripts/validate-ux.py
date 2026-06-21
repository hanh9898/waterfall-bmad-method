#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-14 UX / Screen Design document (structure only).

Checks required sections (English canonical + configured document language — NO
hardcoded Japanese), at least one screen with a well-formed id (SCR-NN),
screen/component id uniqueness (SCR-/CMP-), and at least one REQ reference.
Inline visual values (hex/px) in components are reported as a non-blocking
advisory (visuals should reference DESIGN.md tokens by {path.to.token}).
Semantic adequacy (do screens cover the REQ set? are states complete?) is the
LLM review layer.
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
    ("Screens", "Màn hình"),
    ("Components", "Thành phần"),
    ("Revision History", "Lịch sử sửa đổi"),
]

REQ_RE = re.compile(r"\bREQ-(?:[A-Z0-9]+-)+\d{3,}\b")
# A DEFINITION is an id in the first cell of a table row; ids in other columns
# (a component naming its screen, a state row naming its component) are references.
SCR_DEF_RE = re.compile(r"(?m)^\|\s*(SCR-\d+)\s*\|")
CMP_DEF_RE = re.compile(r"(?m)^\|\s*(CMP-\d+)\s*\|")
INLINE_VISUAL_RE = re.compile(r"#[0-9a-fA-F]{3,6}\b|\b\d+px\b")


def check_sections(content: str) -> list[dict]:
    issues: list[dict] = []
    for en_name, lang_name in REQUIRED_SECTIONS:
        match = find_section(content, en_name, lang_name)
        if not match:
            issues.append({"type": "SECTION_MISSING",
                           "message": f"Required section '{en_name}' / '{lang_name}' not found",
                           "section": en_name, "auto_fixable": False})
        elif not section_has_content(section_body(content, match)):
            issues.append({"type": "SECTION_EMPTY",
                           "message": f"Section '{en_name}' is empty",
                           "section": en_name, "auto_fixable": False})
    return issues


def check_elements(content: str) -> tuple[list[dict], int, int]:
    """Count DEFINITIONS only: SCR ids defined (first table cell) in the Screens
    section, CMP ids defined in the Components section. Ids appearing in other
    columns/sections are references and must not be counted (else a component
    naming its screen, or a state row naming its component, looks like a dup)."""
    scr_match = find_section(content, "Screens", "Màn hình")
    cmp_match = find_section(content, "Components", "Thành phần")
    screen_defs = SCR_DEF_RE.findall(section_body(content, scr_match)) if scr_match else []
    comp_defs = CMP_DEF_RE.findall(section_body(content, cmp_match)) if cmp_match else []

    issues: list[dict] = []
    if not screen_defs:
        issues.append({"type": "NO_SCREEN",
                       "message": "No screen defined (expected SCR-NN row in the Screens table)",
                       "auto_fixable": False})
    for d, n in Counter(screen_defs + comp_defs).items():
        if n > 1:
            issues.append({"type": "DUPLICATE_ELEMENT_ID",
                           "message": f"Duplicate element id: '{d}'",
                           "element": d, "auto_fixable": False})
    return issues, len(set(screen_defs)), len(set(comp_defs))


def check_req_refs(content: str) -> list[dict]:
    if not REQ_RE.search(content):
        return [{"type": "NO_REQ_REF",
                 "message": "No REQ-<FEAT>-NNN reference — each screen must name its requirement",
                 "auto_fixable": False}]
    return []


def find_advisories(content: str) -> list[dict]:
    """Non-blocking: inline visual values in the Components section."""
    advisories: list[dict] = []
    match = find_section(content, "Components", "Thành phần")
    if match:
        body = section_body(content, match)
        if INLINE_VISUAL_RE.search(body):
            advisories.append({
                "type": "INLINE_VISUAL_VALUE",
                "message": "Inline hex/px in Components — reference DESIGN.md tokens by {path.to.token} instead",
                "auto_fixable": False,
            })
    return advisories


CHECKED = [
    "required sections present and non-empty",
    "at least one screen (SCR-NN) with well-formed id",
    "screen/component id uniqueness",
    "at least one REQ reference",
]
NOT_CHECKED = [
    "screens cover every UI-facing REQ (LLM review)",
    "states complete, not only happy path (LLM review)",
    "D-14 <-> Claude Design mockup consistency (LLM review / readiness)",
]


def validate(doc_path: str) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    issues: list[dict] = []
    issues.extend(check_sections(content))
    elem_issues, screen_count, component_count = check_elements(content)
    issues.extend(elem_issues)
    issues.extend(check_req_refs(content))
    advisories = find_advisories(content)

    structure_ok = len(issues) == 0
    result = verdict(structure_ok, semantic_review=SEMANTIC_NA, checked=CHECKED, not_checked=NOT_CHECKED)
    result.update({
        "valid": structure_ok,
        "total_issues": len(issues),
        "auto_fixable_count": len([i for i in issues if i.get("auto_fixable")]),
        "manual_fix_count": len([i for i in issues if not i.get("auto_fixable")]),
        "advisory_count": len(advisories),
        "screen_count": screen_count,
        "component_count": component_count,
        "issues": issues,
        "advisories": advisories,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate D-14 UX / Screen Design document.")
    parser.add_argument("document", help="Path to D-14 document")
    parser.add_argument("--project-root", required=True, help="Project root directory")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(json.dumps({
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-create-ux' first to generate D-14.",
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
