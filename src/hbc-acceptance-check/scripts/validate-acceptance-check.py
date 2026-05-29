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
from pathlib import Path

REQUIRED_SECTIONS = [
    ("受入基準チェックリスト", "Acceptance Criteria Checklist"),
    ("トレーサビリティサマリー", "Traceability Summary"),
    ("決定", "Decision"),
]

VALID_DECISIONS = {"ACCEPTED", "REJECTED", "DEFERRED", "PENDING"}

DECISION_RE = re.compile(
    r"\*\*(?:Status|ステータス):\*\*\s*(ACCEPTED|REJECTED|DEFERRED|PENDING)",
    re.IGNORECASE,
)

DECIDED_BY_RE = re.compile(
    r"\*\*(?:Decided by|決定者):\*\*[ \t]*(.+)",
    re.IGNORECASE,
)

REASON_RE = re.compile(
    r"\*\*(?:Reason|理由):\*\*[ \t]*(.+)",
    re.IGNORECASE,
)


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

    return issues


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
            r"#+\s.*(?:Action Items|アクションアイテム)",
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
        r"#+\s.*(?:受入基準チェックリスト|Acceptance Criteria Checklist)(.*?)(?=\n#|\Z)",
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
        if "Criterion" in r or "Status" in r or "基準" in r
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
        r"#+\s.*(?:トレーサビリティサマリー|Traceability Summary)(.*?)(?=\n#|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not trace_match:
        return issues

    trace_body = trace_match.group(1)
    has_total = bool(
        re.search(r"(?:Total Requirements|総要件数)", trace_body, re.IGNORECASE)
    )
    has_coverage = bool(
        re.search(r"(?:Trace Coverage|トレースカバレッジ)", trace_body, re.IGNORECASE)
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

    return {
        "valid": len(all_issues) == 0,
        "total_issues": len(all_issues),
        "decision": decision,
        "issues": all_issues,
    }


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
