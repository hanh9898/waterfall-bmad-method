#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-08 Architecture Design document (structure only).

Checks required sections present + non-empty (English canonical + configured
document language — NO hardcoded Japanese), at least one REQ reference, and that
every Decision Record (ADR) carries a rationale. Semantic adequacy (are the
decisions *justified*, do components cover the REQ set) is the LLM review layer.

Shares table/section/verdict primitives with the HBC validation library.
"""

import argparse
import json
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

# --- shared lib bootstrap ---
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

# (English canonical, configured-language label). No Japanese.
REQUIRED_SECTIONS = [
    ("Overview", "Tổng quan"),
    ("Components", "Thành phần"),
    ("Integration Points", "Điểm tích hợp"),
    ("Decision Records", "Bản ghi quyết định"),
    ("Revision History", "Lịch sử sửa đổi"),
]

REQ_RE = re.compile(r"\bREQ-(?:[A-Z0-9]+-)+\d{3,}\b")
ADR_HEADING_RE = re.compile(r"^#{2,4}\s+ADR-\d+", re.MULTILINE)
RATIONALE_RE = re.compile(r"(?im)^\s*[-*]?\s*\*{0,2}(Rationale|Lý do)\*{0,2}\s*:\s*\S+")


def check_sections(content: str) -> list[dict]:
    issues: list[dict] = []
    for en_name, lang_name in REQUIRED_SECTIONS:
        match = find_section(content, en_name, lang_name)
        if not match:
            issues.append({
                "type": "SECTION_MISSING",
                "message": f"Required section '{en_name}' / '{lang_name}' not found",
                "section": en_name,
                "auto_fixable": False,
            })
            continue
        if not section_has_content(section_body(content, match)):
            issues.append({
                "type": "SECTION_EMPTY",
                "message": f"Section '{en_name}' is empty",
                "section": en_name,
                "auto_fixable": False,
            })
    return issues


def check_req_refs(content: str) -> list[dict]:
    if not REQ_RE.search(content):
        return [{
            "type": "NO_REQ_REF",
            "message": "No REQ-<FEAT>-NNN reference found — components/decisions must trace to requirements",
            "auto_fixable": False,
        }]
    return []


def check_adr_rationale(content: str) -> tuple[list[dict], int]:
    """Each ADR heading must be followed by a Rationale line before the next ADR.

    Scan is bounded to the Decision Records section so the LAST ADR's block does
    not bleed into following sections (e.g. Revision History) and false-pass on a
    stray 'Rationale:' there.
    """
    dr_match = find_section(content, "Decision Records", "Bản ghi quyết định")
    scope = section_body(content, dr_match) if dr_match else ""
    issues: list[dict] = []
    headings = list(ADR_HEADING_RE.finditer(scope))
    for i, h in enumerate(headings):
        start = h.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(scope)
        block = scope[start:end]
        if not RATIONALE_RE.search(block):
            title = scope[h.start():start].strip()
            issues.append({
                "type": "ADR_NO_RATIONALE",
                "message": f"Decision Record '{title}' has no Rationale",
                "auto_fixable": False,
            })
    return issues, len(headings)


CHECKED = [
    "required sections present and non-empty",
    "at least one REQ reference",
    "every Decision Record (ADR) has a rationale",
]
NOT_CHECKED = [
    "decisions are justified / components cover REQ set (LLM review)",
    "integration points grounded in the real system (LLM review)",
    "NFR decisions traceable to measurable NFRs (LLM review)",
]


def validate(doc_path: str) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    issues: list[dict] = []
    issues.extend(check_sections(content))
    issues.extend(check_req_refs(content))
    adr_issues, adr_count = check_adr_rationale(content)
    issues.extend(adr_issues)

    structure_ok = len(issues) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=CHECKED,
        not_checked=NOT_CHECKED,
    )
    result.update({
        "valid": structure_ok,
        "total_issues": len(issues),
        "auto_fixable_count": len([i for i in issues if i.get("auto_fixable")]),
        "manual_fix_count": len([i for i in issues if not i.get("auto_fixable")]),
        "adr_count": adr_count,
        "issues": issues,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate D-08 Architecture Design document.")
    parser.add_argument("document", help="Path to D-08 document")
    parser.add_argument("--project-root", required=True, help="Project root directory")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(json.dumps({
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-create-architecture' first to generate D-08.",
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
