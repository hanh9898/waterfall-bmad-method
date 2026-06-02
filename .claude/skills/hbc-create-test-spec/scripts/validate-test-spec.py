#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-27 Test Specification document.

Checks TC ID uniqueness, REQ-xxx coverage, required fields per test case,
and returns structured JSON with per-issue auto_fixable flag.
"""

import argparse
import json
import re
import sys
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
    ("Test Case Summary", "Danh sách test case"),
    ("Detailed Test Cases", "Chi tiết test case"),
    ("Coverage Matrix", "Ma trận bao phủ"),
]

TC_ID_RE = re.compile(r"TC-(\d{3,})")
REQ_ID_RE = re.compile(r"REQ-(\d{3,})")


def check_sections(content: str) -> list[dict]:
    """Required sections present (presence-only; English or VN label, shared lib)."""
    return check_required_sections(content, REQUIRED_SECTIONS, empty_check=False)


def check_tc_ids(content: str) -> list[dict]:
    issues: list[dict] = []

    heading_tc_re = re.compile(r"^###\s+TC-(\d{3,}):", re.MULTILINE)
    heading_matches = heading_tc_re.findall(content)

    all_mentions = TC_ID_RE.findall(content)
    if not all_mentions:
        issues.append({
            "type": "NO_TEST_CASES",
            "message": "No TC-xxx IDs found in document",
            "auto_fixable": False,
        })
        return issues

    ids = [int(m) for m in heading_matches] if heading_matches else [int(m) for m in all_mentions]
    unique_ids = sorted(set(ids))

    seen_counts: dict[int, int] = {}
    for tc_num in ids:
        seen_counts[tc_num] = seen_counts.get(tc_num, 0) + 1
    for tc_num, count in seen_counts.items():
        if count > 1:
            issues.append({
                "type": "TC_ID_DUPLICATE",
                "message": f"TC-{tc_num:03d} has {count} heading declarations",
                "auto_fixable": True,
                "tc_id": f"TC-{tc_num:03d}",
            })

    if unique_ids:
        expected = list(range(1, max(unique_ids) + 1))
        missing = [n for n in expected if n not in set(unique_ids)]
        if missing:
            missing_labels = [f"TC-{n:03d}" for n in missing]
            issues.append({
                "type": "TC_ID_GAP",
                "message": f"Non-sequential: missing {', '.join(missing_labels)}",
                "auto_fixable": True,
                "missing_ids": missing_labels,
            })

    return issues


def check_req_coverage(content: str, d02_path: str | None) -> list[dict]:
    issues: list[dict] = []

    if not d02_path:
        return issues

    try:
        d02_content = Path(d02_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return issues

    d02_req_ids = set(REQ_ID_RE.findall(d02_content))
    d27_req_ids = set(REQ_ID_RE.findall(content))

    uncovered = d02_req_ids - d27_req_ids
    for req_num in sorted(uncovered):
        issues.append({
            "type": "REQ_NO_COVERAGE",
            "message": f"REQ-{req_num} from D-02 has no test case in D-27",
            "req_id": f"REQ-{req_num}",
            "auto_fixable": False,
        })

    orphans = d27_req_ids - d02_req_ids
    for req_num in sorted(orphans):
        issues.append({
            "type": "ORPHAN_REQ_REF",
            "message": f"REQ-{req_num} referenced in D-27 but not found in D-02",
            "req_id": f"REQ-{req_num}",
            "auto_fixable": False,
        })

    return issues


def check_tc_fields(content: str) -> list[dict]:
    issues: list[dict] = []

    tc_headings = list(re.finditer(r"###\s+TC-(\d{3,}):", content))

    for i, match in enumerate(tc_headings):
        tc_id = f"TC-{match.group(1)}"
        start = match.end()
        end = tc_headings[i + 1].start() if i + 1 < len(tc_headings) else len(content)
        tc_body = content[start:end]

        if not re.search(r"\*\*REQ ID:\*\*", tc_body):
            issues.append({
                "type": "TC_MISSING_REQ",
                "message": f"{tc_id}: missing REQ ID field",
                "tc_id": tc_id,
                "auto_fixable": False,
            })

        if not re.search(r"\*\*Severity:\*\*", tc_body):
            issues.append({
                "type": "TC_MISSING_SEVERITY",
                "message": f"{tc_id}: missing Severity field",
                "tc_id": tc_id,
                "auto_fixable": False,
            })

        step_rows = re.findall(r"\|\s*\d+\s*\|[^|]+\|[^|]+\|", tc_body)
        if len(step_rows) < 1:
            issues.append({
                "type": "TC_NO_STEPS",
                "message": f"{tc_id}: no test steps found",
                "tc_id": tc_id,
                "auto_fixable": False,
            })

    return issues


def validate(doc_path: str, d02_path: str | None = None) -> dict:
    content = Path(doc_path).read_text(encoding="utf-8")

    all_issues: list[dict] = []
    all_issues.extend(check_sections(content))
    all_issues.extend(check_tc_ids(content))
    all_issues.extend(check_req_coverage(content, d02_path))
    all_issues.extend(check_tc_fields(content))

    auto_fixable = [i for i in all_issues if i.get("auto_fixable")]
    manual_fix = [i for i in all_issues if not i.get("auto_fixable")]

    tc_ids = set(TC_ID_RE.findall(content))
    d02_req_ids = set()
    if d02_path:
        try:
            d02_req_ids = set(REQ_ID_RE.findall(
                Path(d02_path).read_text(encoding="utf-8")
            ))
        except (OSError, UnicodeDecodeError):
            pass

    d27_req_ids = set(REQ_ID_RE.findall(content))
    covered = len(d02_req_ids & d27_req_ids) if d02_req_ids else 0
    total_reqs = len(d02_req_ids) if d02_req_ids else 0
    coverage_pct = round(covered / total_reqs * 100) if total_reqs > 0 else 0

    structure_ok = len(all_issues) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=["required sections", "TC id uniqueness", "REQ coverage vs D-02", "required fields per TC"],
        not_checked=["test-case adequacy / đủ-nghĩa (LLM review)", "REQ facet coverage read/write·api/admin (LLM review)"],
    )
    result.update({
        "valid": structure_ok,
        "total_issues": len(all_issues),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "tc_count": len(tc_ids),
        "req_coverage_pct": coverage_pct,
        "issues": all_issues,
    })
    return result


def main():
    parser = argparse.ArgumentParser(description="Validate D-27 Test Specification.")
    parser.add_argument("document", help="Path to D-27 test spec document")
    parser.add_argument("--d02", help="Path to D-02 requirements (for coverage check)")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        error = {
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-create-test-spec' first to generate D-27.",
        }
        print(json.dumps(error, indent=2, ensure_ascii=False))
        sys.exit(1)

    result = validate(str(doc_path), args.d02)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
