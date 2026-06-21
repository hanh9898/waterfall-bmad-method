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

# --- shared lib bootstrap (Batch 0 / C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        check_required_sections,
        churn_assessment,
        find_section,
        parse_table,
        verdict,
    )
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

    # Section presence is handled by check_sections (REQUIRED_SECTIONS). Here we
    # only assert the risk table has data rows. parse_table is language-aware
    # (English heading OR configured-language alias) and returns DATA rows only
    # (header + separator excluded), so a header-only table reports zero rows.
    if not find_section(content, "Risk", "Quản lý rủi ro"):
        return issues

    if len(parse_table(content, "Risk", "Quản lý rủi ro")) < 1:
        issues.append({
            "type": "EMPTY_RISK_TABLE",
            "message": "Risk table has no data rows — identify at least 1 testing risk",
            "auto_fixable": False,
        })

    return issues


def check_schedule(content: str) -> list[dict]:
    issues: list[dict] = []

    has_gantt = "gantt" in content.lower() and "mermaid" in content.lower()
    # Milestone table lives under the Schedule section (e.g. "### 7.1 Milestones").
    # parse_table is language-aware and returns its data rows, so a VN milestone
    # table ("Cột mốc …") counts the same as an English one.
    has_milestone_table = len(parse_table(content, "Schedule", "Lịch trình")) >= 1

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
        not_checked=[
            "test strategy adequacy (LLM review)",
            "admin/lifecycle test-area fencing (LLM review)",
            "risk likelihood/impact realistic + USER-confirmed (B9-2, domain decision)",
            "schedule grounding + technique-per-scope-area (B9-1/B9-4 — see check-test-plan-grounding.py)",
            "in/out-scope confirmed with user before generation (B9-3, ASK-before-generate)",
        ],
    )
    result.update({
        "valid": structure_ok,
        "total_issues": len(all_issues),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "section_count": section_count,
        # T2.11 anti-churn: revision-history count vs threshold. high_churn is the
        # cue the skill surfaces to suggest maturity=exploratory / [DSC] instead of
        # bumping the version on every small edit (per-session bump policy).
        "churn": churn_assessment(content),
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
