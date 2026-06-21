#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a discovery-note document (structure only).

Checks required sections (English canonical + configured document language — NO
hardcoded Japanese), at least one risk assumption (ASM-NN), a valid verdict token
(VALIDATED / RESHAPE / KILL), a filled USER sign-off, and — when the verdict is
RESHAPE or KILL — a REQ Impact section naming ≥1 requirement.

Out of scope for this script (LLM / USER review layer): whether the validation
was actually run against ground-truth (not the draft), whether the evidence is a
real falsification attempt, and whether the verdict is honestly supported. The
sign-off is the USER's responsibility; this script only checks it is present.
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
    ("Riskiest Assumptions", "Giả định rủi ro nhất"),
    ("Validation Method", "Phương pháp kiểm chứng"),
    ("Evidence", "Bằng chứng"),
    ("Verdict", "Kết luận"),
    ("Revision History", "Lịch sử sửa đổi"),
]

HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
REQ_RE = re.compile(r"\bREQ-(?:[A-Z0-9]+-)+\d{3,}\b")
# An assumption DEFINITION is an ASM-NN id in the first cell of a table row.
ASM_RE = re.compile(r"(?m)^\|\s*(ASM)-(\d+)\s*\|")
# NOTE: use [ \t]* (not \s*) for in-line whitespace — \s matches newlines, so an
# empty value would let the pattern swallow the blank line and capture the NEXT
# line's content (a missing sign-off would look filled).
VERDICT_RE = re.compile(r"(?im)^[ \t]*\**[ \t]*Verdict[ \t]*:?\**[ \t]*(VALIDATED|RESHAPE|KILL)\b")
SIGNOFF_RE = re.compile(r"(?im)^[ \t]*\**[ \t]*Signed-off-by[ \t]*:?\**[ \t]*(.*)$")
PLACEHOLDER = re.compile(r"^(tbd|n/?a|-|—|\.\.\.)?$", re.IGNORECASE)


def strip_comments(content: str) -> str:
    return HTML_COMMENT_RE.sub("", content)


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


def check_assumptions(content: str) -> tuple[list[dict], int]:
    ids = [f"{m.group(1)}-{m.group(2)}" for m in ASM_RE.finditer(content)]
    issues: list[dict] = []
    if not ids:
        issues.append({
            "type": "NO_ASSUMPTION",
            "message": "No risk assumption found (expected an ASM-NN row in Riskiest Assumptions)",
            "auto_fixable": False,
        })
    for d in [a for a, n in Counter(ids).items() if n > 1]:
        issues.append({
            "type": "DUPLICATE_ASSUMPTION_ID",
            "message": f"Duplicate assumption id: '{d}'",
            "element": d, "auto_fixable": False,
        })
    return issues, len(set(ids))


def check_verdict_and_signoff(content: str) -> tuple[list[dict], str | None]:
    issues: list[dict] = []
    vmatch = VERDICT_RE.search(content)
    verdict_value = vmatch.group(1).upper() if vmatch else None
    if not verdict_value:
        issues.append({
            "type": "INVALID_VERDICT",
            "message": "No valid verdict — expected 'Verdict: VALIDATED | RESHAPE | KILL'",
            "auto_fixable": False,
        })

    smatch = SIGNOFF_RE.search(content)
    signoff = smatch.group(1).strip() if smatch else ""
    if not smatch or PLACEHOLDER.match(signoff):
        issues.append({
            "type": "SIGNOFF_MISSING",
            "message": "USER sign-off is empty — the verdict requires a human sign-off (the LLM must not self-certify)",
            "auto_fixable": False,
        })
    return issues, verdict_value


def check_req_impact(content: str, verdict_value: str | None) -> list[dict]:
    if verdict_value not in ("RESHAPE", "KILL"):
        return []
    match = find_section(content, "REQ Impact", "Ảnh hưởng REQ")
    body = section_body(content, match) if match else ""
    if not match or not REQ_RE.search(body):
        return [{
            "type": "REQ_IMPACT_MISSING",
            "message": f"Verdict {verdict_value} requires a REQ Impact section naming ≥1 REQ-<FEAT>-NNN to revise/drop",
            "auto_fixable": False,
        }]
    return []


CHECKED = [
    "required sections present and non-empty",
    "at least one risk assumption (ASM-NN)",
    "verdict token valid (VALIDATED / RESHAPE / KILL)",
    "USER sign-off present (not a placeholder)",
    "RESHAPE/KILL verdict names ≥1 REQ in REQ Impact",
]
NOT_CHECKED = [
    "validation was run against ground-truth, not the draft (LLM / USER review)",
    "evidence is a real falsification attempt (LLM / USER review)",
    "the verdict is honestly supported by the evidence (USER sign-off)",
]


def validate(doc_path: str) -> dict:
    raw = Path(doc_path).read_text(encoding="utf-8")
    content = strip_comments(raw)

    issues: list[dict] = []
    issues.extend(check_sections(content))
    # Count ASM DEFINITIONS only inside the owning section; ASM-NN that appears in
    # the Validation Method / Evidence tables is a reference, not a definition.
    asm_match = find_section(content, "Riskiest Assumptions", "Giả định rủi ro nhất")
    asm_scope = section_body(content, asm_match) if asm_match else ""
    asm_issues, assumption_count = check_assumptions(asm_scope)
    issues.extend(asm_issues)
    vs_issues, verdict_value = check_verdict_and_signoff(content)
    issues.extend(vs_issues)
    issues.extend(check_req_impact(content, verdict_value))

    structure_ok = len(issues) == 0
    result = verdict(structure_ok, semantic_review=SEMANTIC_NA, checked=CHECKED, not_checked=NOT_CHECKED)
    result.update({
        "valid": structure_ok,
        "total_issues": len(issues),
        "auto_fixable_count": len([i for i in issues if i.get("auto_fixable")]),
        "manual_fix_count": len([i for i in issues if not i.get("auto_fixable")]),
        "assumption_count": assumption_count,
        "verdict_value": verdict_value,
        "issues": issues,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate a discovery-note document.")
    parser.add_argument("document", help="Path to discovery-note document")
    parser.add_argument("--project-root", required=True, help="Project root directory")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(json.dumps({
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-discovery-spike' first to generate the discovery-note.",
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
