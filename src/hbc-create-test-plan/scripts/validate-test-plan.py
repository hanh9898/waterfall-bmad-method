#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-26 Test Plan document.

Checks required sections, entry/exit criteria, risk table,
and schedule presence.
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
    ("Overview", "Tổng quan"),
    ("Test Scope", "Phạm vi kiểm thử"),
    ("Test Levels", "Cấp độ kiểm thử"),
    ("Test Approach", "Phương pháp kiểm thử"),
    ("Test Environment", "Môi trường kiểm thử"),
    ("Entry", "Tiêu chí vào/ra"),
    ("Schedule", "Lịch trình"),
    ("Team", "Đội ngũ / vai trò"),
    ("Risk", "Quản lý rủi ro"),
    ("Deliverables", "Sản phẩm bàn giao"),
]


def check_sections(content: str) -> list[dict]:
    """Required sections present + non-empty (shared lib; English or VN label)."""
    return check_required_sections(content, REQUIRED_SECTIONS, empty_check=True)


def check_entry_exit_criteria(content: str) -> list[dict]:
    issues: list[dict] = []

    entry_match = re.search(r"#+\s.*(?:Entry Criteria|Tiêu chí vào)", content, re.IGNORECASE)
    exit_match = re.search(r"#+\s.*(?:Exit Criteria|Tiêu chí ra)", content, re.IGNORECASE)

    if not entry_match:
        issues.append({
            "type": "NO_ENTRY_CRITERIA",
            "message": "Entry criteria section not found — must define when testing can begin",
            "auto_fixable": False,
        })

    if not exit_match:
        issues.append({
            "type": "NO_EXIT_CRITERIA",
            "message": "Exit criteria section not found — must define when testing is complete",
            "auto_fixable": False,
        })

    return issues


def check_risk_table(content: str) -> list[dict]:
    issues: list[dict] = []

    risk_match = re.search(r"#+\s.*Risk", content, re.IGNORECASE)
    if not risk_match:
        return issues

    start = risk_match.end()
    next_section = re.search(r"\n##\s", content[start:])
    risk_body = content[start : start + next_section.start()] if next_section else content[start:]

    risk_rows = re.findall(r"\|\s*[^|\-][^|]*\|[^|]*\|[^|]*\|[^|]*\|", risk_body)
    header_count = sum(1 for r in risk_rows if "Risk" in r or "Likelihood" in r)
    data_rows = len(risk_rows) - header_count

    if data_rows < 1:
        issues.append({
            "type": "EMPTY_RISK_TABLE",
            "message": "Risk table has no data rows — identify at least 1 testing risk",
            "auto_fixable": False,
        })

    return issues


def check_schedule(content: str) -> list[dict]:
    issues: list[dict] = []

    has_gantt = "gantt" in content.lower() and "mermaid" in content.lower()
    has_milestone_table = bool(
        re.search(r"\|\s*Milestone\s*\|", content, re.IGNORECASE)
    )

    if not has_gantt and not has_milestone_table:
        issues.append({
            "type": "NO_SCHEDULE",
            "message": "No schedule visualization found — add a Gantt chart or milestone table",
            "auto_fixable": True,
        })

    return issues


def validate(doc_path: str) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    all_issues: list[dict] = []
    all_issues.extend(check_sections(content))
    all_issues.extend(check_entry_exit_criteria(content))
    all_issues.extend(check_risk_table(content))
    all_issues.extend(check_schedule(content))

    auto_fixable = [i for i in all_issues if i.get("auto_fixable")]
    manual_fix = [i for i in all_issues if not i.get("auto_fixable")]

    section_count = len(re.findall(r"^##\s", content, re.MULTILINE))

    structure_ok = len(all_issues) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=["required sections", "entry/exit criteria", "risk table", "schedule presence"],
        not_checked=["test strategy adequacy (LLM review)", "admin/lifecycle test-area fencing (LLM review)"],
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
    parser = argparse.ArgumentParser(description="Validate D-26 Test Plan.")
    parser.add_argument("document", help="Path to D-26 test plan document")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        error = {
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-create-test-plan' first to generate D-26.",
        }
        print(json.dumps(error, indent=2, ensure_ascii=False))
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
