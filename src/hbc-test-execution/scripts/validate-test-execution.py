#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a test execution report.

Checks required sections, summary table presence and values,
defect triage completeness, and coverage threshold.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("テスト実行サマリー", "Test Execution Summary"),
    ("失敗テスト詳細", "Failed Tests Detail"),
    ("不具合トリアージ", "Defect Triage"),
]

VALID_CLASSIFICATIONS = {"code_bug", "test_bug", "missing_coverage", "environment", "spec_issue"}

SUMMARY_METRICS_RE = re.compile(
    r"\|\s*(?:Total Tests|総テスト数)\s*\|\s*(\d+)\s*\|", re.IGNORECASE
)
PASSED_RE = re.compile(r"\|\s*(?:Passed|成功)\s*\|\s*(\d+)\s*\|", re.IGNORECASE)
FAILED_RE = re.compile(r"\|\s*(?:Failed|失敗)\s*\|\s*(\d+)\s*\|", re.IGNORECASE)
COVERAGE_RE = re.compile(
    r"\|\s*(?:Coverage|カバレッジ)\s*\|\s*([\d.]+)%?\s*\|", re.IGNORECASE
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


def check_summary(content: str) -> list[dict]:
    issues: list[dict] = []

    total_match = SUMMARY_METRICS_RE.search(content)
    if not total_match:
        issues.append({
            "type": "NO_SUMMARY_TOTAL",
            "message": "Test execution summary missing Total Tests count",
            "auto_fixable": False,
        })
        return issues

    total = int(total_match.group(1))
    if total == 0:
        issues.append({
            "type": "ZERO_TESTS",
            "message": "Total Tests is 0 — no tests were executed",
            "auto_fixable": False,
        })

    passed_match = PASSED_RE.search(content)
    failed_match = FAILED_RE.search(content)

    if not passed_match:
        issues.append({
            "type": "NO_PASSED_COUNT",
            "message": "Summary missing Passed count",
            "auto_fixable": False,
        })
    if not failed_match:
        issues.append({
            "type": "NO_FAILED_COUNT",
            "message": "Summary missing Failed count",
            "auto_fixable": False,
        })

    if passed_match and failed_match and total > 0:
        passed = int(passed_match.group(1))
        failed = int(failed_match.group(1))
        if passed + failed > total:
            issues.append({
                "type": "INCONSISTENT_COUNTS",
                "message": f"Passed ({passed}) + Failed ({failed}) exceeds Total ({total})",
                "auto_fixable": True,
            })

    return issues


def check_coverage(content: str, threshold: float) -> list[dict]:
    issues: list[dict] = []

    cov_match = COVERAGE_RE.search(content)
    if not cov_match:
        issues.append({
            "type": "NO_COVERAGE",
            "message": "Coverage percentage not found in summary",
            "auto_fixable": False,
        })
        return issues

    coverage = float(cov_match.group(1))
    if coverage < threshold:
        issues.append({
            "type": "COVERAGE_BELOW_THRESHOLD",
            "message": f"Coverage {coverage}% below threshold {threshold}%",
            "auto_fixable": False,
        })

    return issues


def check_defect_triage(content: str) -> list[dict]:
    issues: list[dict] = []

    failed_match = FAILED_RE.search(content)
    if not failed_match:
        return issues

    failed_count = int(failed_match.group(1))
    if failed_count == 0:
        return issues

    triage_section = re.search(
        r"#+\s.*(?:不具合トリアージ|Defect Triage)(.*?)(?=\n#|\Z)",
        content,
        re.DOTALL | re.IGNORECASE,
    )
    if not triage_section:
        issues.append({
            "type": "NO_TRIAGE_FOR_FAILURES",
            "message": f"{failed_count} tests failed but no Defect Triage section found",
            "auto_fixable": False,
        })
        return issues

    triage_body = triage_section.group(1)
    defect_rows = re.findall(r"\|\s*DEF-\d+\s*\|", triage_body)

    if len(defect_rows) < failed_count:
        issues.append({
            "type": "INCOMPLETE_TRIAGE",
            "message": f"{failed_count} failures but only {len(defect_rows)} defects triaged",
            "auto_fixable": False,
        })

    return issues


def validate(doc_path: str, coverage_threshold: float = 80.0) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    all_issues: list[dict] = []
    all_issues.extend(check_sections(content))
    all_issues.extend(check_summary(content))
    all_issues.extend(check_coverage(content, coverage_threshold))
    all_issues.extend(check_defect_triage(content))

    total_match = SUMMARY_METRICS_RE.search(content)
    passed_match = PASSED_RE.search(content)
    failed_match = FAILED_RE.search(content)
    cov_match = COVERAGE_RE.search(content)

    return {
        "valid": len(all_issues) == 0,
        "total_issues": len(all_issues),
        "summary": {
            "total": int(total_match.group(1)) if total_match else 0,
            "passed": int(passed_match.group(1)) if passed_match else 0,
            "failed": int(failed_match.group(1)) if failed_match else 0,
            "coverage_pct": float(cov_match.group(1)) if cov_match else 0.0,
        },
        "issues": all_issues,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate test execution report.")
    parser.add_argument("document", help="Path to test-execution-report.md")
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Coverage threshold (default: 80)",
    )
    parser.add_argument("-o", "--output", help="Output file")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(json.dumps({"error": f"Not found: {args.document}"}))
        sys.exit(1)

    result = validate(str(doc_path), args.threshold)
    text = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
