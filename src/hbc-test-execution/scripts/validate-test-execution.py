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

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

# --- shared lib bootstrap (Đợt 0 / C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        check_required_sections,
        strip_code_fences,
        tc_ids,
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
    ("Test Execution Summary", "Tóm tắt thực thi kiểm thử"),
    ("Failed Tests Detail", "Chi tiết test thất bại"),
    ("Defect Triage", "Phân loại lỗi"),
]

VALID_CLASSIFICATIONS = {"code_bug", "test_bug", "missing_coverage", "environment", "spec_issue"}

SUMMARY_METRICS_RE = re.compile(
    r"\|\s*Total Tests\s*\|\s*(\d+)\s*\|", re.IGNORECASE
)
PASSED_RE = re.compile(r"\|\s*Passed\s*\|\s*(\d+)\s*\|", re.IGNORECASE)
FAILED_RE = re.compile(r"\|\s*Failed\s*\|\s*(\d+)\s*\|", re.IGNORECASE)
COVERAGE_RE = re.compile(
    r"\|\s*Coverage\s*\|\s*([\d.]+)%?\s*\|", re.IGNORECASE
)


def check_sections(content: str) -> list[dict]:
    """Required sections present (presence-only; English or VN label, shared lib)."""
    return check_required_sections(content, REQUIRED_SECTIONS, empty_check=False)


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
        r"#+\s.*Defect Triage(.*?)(?=\n#|\Z)",
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


def check_tc_reconciliation(content: str, d27_path: str | None) -> list[dict]:
    """Reconcile EXECUTED TCs (referenced in the report) against SPECIFIED TCs
    (declared in D-27) — closes the Phase 3→4 seam where "all passed" can hide
    spec'd tests that were never run (D1). Deterministic TC-id set diff."""
    issues: list[dict] = []
    if not d27_path:
        return issues
    try:
        d27_content = Path(d27_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        issues.append({
            "type": "D27_UNREADABLE",
            "message": f"--d27 provided but not readable: {d27_path}",
            "auto_fixable": False,
        })
        return issues

    specified = tc_ids(d27_content)
    executed = {f"TC-{m}" for m in re.findall(r"TC-(\d{3,})", strip_code_fences(content))}

    for tc in sorted(specified - executed):
        issues.append({
            "type": "TC_UNEXECUTED",
            "message": f"{tc} specified in D-27 but no result in the execution report",
            "tc_id": tc,
            "auto_fixable": False,
        })
    for tc in sorted(executed - specified):
        issues.append({
            "type": "TC_PHANTOM_RESULT",
            "message": f"{tc} has a result but is not specified in D-27",
            "tc_id": tc,
            "auto_fixable": False,
        })
    return issues


def validate(doc_path: str, coverage_threshold: float = 80.0, d27_path: str | None = None) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    all_issues: list[dict] = []
    all_issues.extend(check_sections(content))
    all_issues.extend(check_summary(content))
    all_issues.extend(check_coverage(content, coverage_threshold))
    all_issues.extend(check_defect_triage(content))
    all_issues.extend(check_tc_reconciliation(content, d27_path))

    total_match = SUMMARY_METRICS_RE.search(content)
    passed_match = PASSED_RE.search(content)
    failed_match = FAILED_RE.search(content)
    cov_match = COVERAGE_RE.search(content)

    structure_ok = len(all_issues) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=["required sections", "summary metrics present/consistent", "defect triage", "coverage threshold", "executed TCs ↔ D-27 specified TCs (if --d27)"],
        not_checked=["root-cause classification correctness (LLM review)", "acceptance decision (acceptance-check)", "whether a reported pass/fail is truthful (LLM review)"],
    )
    result.update({
        "valid": structure_ok,
        "total_issues": len(all_issues),
        "summary": {
            "total": int(total_match.group(1)) if total_match else 0,
            "passed": int(passed_match.group(1)) if passed_match else 0,
            "failed": int(failed_match.group(1)) if failed_match else 0,
            "coverage_pct": float(cov_match.group(1)) if cov_match else 0.0,
        },
        "issues": all_issues,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate test execution report.")
    parser.add_argument("document", help="Path to test-execution-report.md")
    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="Coverage threshold (default: 80)",
    )
    parser.add_argument(
        "--d27",
        help="Path to D-27 test spec — reconcile executed TCs against specified TCs (D1)",
    )
    parser.add_argument("-o", "--output", help="Output file")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        print(json.dumps({"error": f"Not found: {args.document}"}))
        sys.exit(1)

    result = validate(str(doc_path), args.threshold, d27_path=args.d27)
    text = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
