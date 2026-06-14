#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate an acceptance report.

Checks required sections, decision validity, criteria checklist,
and traceability summary presence.
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

# --- shared lib bootstrap (Đợt 0 / C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import SEMANTIC_NA, check_required_sections, verdict  # noqa: E402
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install the hbc-shared component alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

# (English canonical, configured-language label). No hardcoded Japanese.
REQUIRED_SECTIONS = [
    ("Acceptance Criteria Checklist", "Danh sách tiêu chí nghiệm thu"),
    ("Traceability Summary", "Tóm tắt truy vết"),
    ("Decision", "Quyết định"),
]

VALID_DECISIONS = {"ACCEPTED", "REJECTED", "DEFERRED", "PENDING"}

DECISION_RE = re.compile(
    r"\*\*(?:Status|Trạng thái):\*\*\s*(ACCEPTED|REJECTED|DEFERRED|PENDING)",
    re.IGNORECASE,
)

DECIDED_BY_RE = re.compile(
    r"\*\*(?:Decided by|Người quyết định):\*\*[ \t]*(.+)",
    re.IGNORECASE,
)

REASON_RE = re.compile(
    r"\*\*(?:Reason|Lý do):\*\*[ \t]*(.+)",
    re.IGNORECASE,
)


def check_sections(content: str) -> list[dict]:
    """Required sections present (presence-only; English or VN label, shared lib)."""
    return check_required_sections(content, REQUIRED_SECTIONS, empty_check=False)


def check_decision(content: str) -> list[dict]:
    issues: list[dict] = []

    decision_match = DECISION_RE.search(content)
    if not decision_match:
        issues.append({
            "type": "NO_DECISION",
            "message": "No acceptance decision found (ACCEPTED/REJECTED/DEFERRED/PENDING)",
            "auto_fixable": False,
        })
        return issues

    decision = decision_match.group(1).upper()
    if decision not in VALID_DECISIONS:
        issues.append({
            "type": "INVALID_DECISION",
            "message": f"Invalid decision '{decision}' — must be one of {VALID_DECISIONS}",
            "auto_fixable": False,
        })

    decided_by_match = DECIDED_BY_RE.search(content)
    if not decided_by_match or not decided_by_match.group(1).strip():
        issues.append({
            "type": "NO_DECIDED_BY",
            "message": "Missing 'Decided by' field — acceptance requires an owner",
            "auto_fixable": False,
        })

    reason_match = REASON_RE.search(content)
    if not reason_match or not reason_match.group(1).strip():
        issues.append({
            "type": "NO_REASON",
            "message": "Missing 'Reason' field — decision must have rationale",
            "auto_fixable": False,
        })

    if decision == "REJECTED":
        action_section = re.search(
            r"#+\s.*(?:Action Items|Hạng mục hành động)",
            content,
            re.IGNORECASE,
        )
        if not action_section:
            issues.append({
                "type": "REJECTED_NO_ACTIONS",
                "message": "Decision is REJECTED but no Action Items section found",
                "auto_fixable": False,
            })

    return issues


def check_criteria_checklist(content: str) -> list[dict]:
    issues: list[dict] = []

    checklist_match = re.search(
        r"#+\s.*(?:Acceptance Criteria Checklist|Danh sách tiêu chí nghiệm thu)(.*?)(?=\n#|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not checklist_match:
        return issues

    checklist_body = checklist_match.group(1)
    criteria_rows = re.findall(
        r"\|\s*[^|\-][^|]*\|[^|]*\|[^|]*\|", checklist_body
    )
    header_count = sum(
        1
        for r in criteria_rows
        if "Criterion" in r or "Status" in r
    )
    data_rows = len(criteria_rows) - header_count

    if data_rows < 1:
        issues.append({
            "type": "EMPTY_CHECKLIST",
            "message": "Acceptance criteria checklist has no data rows",
            "auto_fixable": False,
        })

    return issues


def check_traceability_summary(content: str) -> list[dict]:
    issues: list[dict] = []

    trace_match = re.search(
        r"#+\s.*(?:Traceability Summary|Tóm tắt truy vết)(.*?)(?=\n#|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not trace_match:
        return issues

    trace_body = trace_match.group(1)
    has_total = bool(
        re.search(r"(?:Total Requirements|Tổng số yêu cầu)", trace_body, re.IGNORECASE)
    )
    has_coverage = bool(
        re.search(r"(?:Trace Coverage|Độ bao phủ truy vết)", trace_body, re.IGNORECASE)
    )

    if not has_total:
        issues.append({
            "type": "NO_REQ_TOTAL",
            "message": "Traceability summary missing Total Requirements",
            "auto_fixable": False,
        })
    if not has_coverage:
        issues.append({
            "type": "NO_TRACE_COVERAGE",
            "message": "Traceability summary missing Trace Coverage percentage",
            "auto_fixable": False,
        })

    return issues


def validate(doc_path: str) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    all_issues: list[dict] = []
    all_issues.extend(check_sections(content))
    all_issues.extend(check_decision(content))
    all_issues.extend(check_criteria_checklist(content))
    all_issues.extend(check_traceability_summary(content))

    decision_match = DECISION_RE.search(content)
    decision = decision_match.group(1).upper() if decision_match else None

    structure_ok = len(all_issues) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=["required sections", "decision validity + owner + reason", "criteria checklist non-empty", "traceability summary present"],
        not_checked=["acceptance judgement soundness (LLM/human review)"],
    )
    result.update({
        "valid": structure_ok,
        "total_issues": len(all_issues),
        "decision": decision,
        "issues": all_issues,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate acceptance report.")
    parser.add_argument("document", help="Path to acceptance-report.md")
    parser.add_argument("-o", "--output", help="Output file")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(json.dumps({"error": f"Not found: {args.document}"}))
        sys.exit(1)

    result = validate(str(doc_path))
    text = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
