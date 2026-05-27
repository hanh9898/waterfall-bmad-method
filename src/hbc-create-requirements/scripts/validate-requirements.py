#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-02 Requirements Specification document.

Checks REQ ID uniqueness and sequencing, flags vague terms,
verifies required sections are present and non-empty,
and returns structured JSON with per-issue auto_fixable flag.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    ("プロジェクト概要", "Project Overview"),
    ("スコープ", "Scope"),
    ("ユーザーロール", "User Roles"),
    ("機能要件", "Functional Requirements"),
    ("非機能要件", "Non-Functional Requirements"),
    ("制約と前提条件", "Constraints"),
]

DEFAULT_VAGUE_TERMS = [
    "fast", "easy", "user-friendly", "simple", "good",
    "nice", "efficient", "appropriate", "adequate", "reasonable",
]

REQ_ID_PATTERN = re.compile(r"REQ-(\d{3,})")


def check_req_ids(content: str) -> list[dict]:
    """Validate REQ IDs are unique and sequential."""
    issues: list[dict] = []
    matches = REQ_ID_PATTERN.findall(content)

    if not matches:
        issues.append({
            "type": "REQ_ID_MISSING",
            "message": "No REQ-xxx IDs found in document",
            "auto_fixable": False,
        })
        return issues

    ids = [int(m) for m in matches]
    seen: dict[int, int] = {}
    for i, req_num in enumerate(ids, 1):
        if req_num in seen:
            issues.append({
                "type": "REQ_ID_DUPLICATE",
                "message": f"REQ-{req_num:03d} appears at positions {seen[req_num]} and {i}",
                "auto_fixable": True,
                "req_id": f"REQ-{req_num:03d}",
            })
        else:
            seen[req_num] = i

    expected = list(range(1, max(ids) + 1))
    missing = [n for n in expected if n not in set(ids)]
    if missing:
        missing_labels = [f"REQ-{n:03d}" for n in missing]
        issues.append({
            "type": "REQ_ID_GAP",
            "message": f"Non-sequential: missing {', '.join(missing_labels)}",
            "auto_fixable": True,
            "missing_ids": missing_labels,
        })

    if ids != sorted(ids):
        issues.append({
            "type": "REQ_ID_ORDER",
            "message": "REQ IDs are not in ascending order in the document",
            "auto_fixable": True,
        })

    return issues


def check_vague_terms(content: str, vague_terms: list[str]) -> list[dict]:
    """Flag vague terms in requirement descriptions."""
    issues: list[dict] = []
    lines = content.splitlines()

    for line_num, line in enumerate(lines, 1):
        lower_line = line.lower()
        for term in vague_terms:
            if re.search(rf"\b{re.escape(term)}\b", lower_line):
                issues.append({
                    "type": "VAGUE_TERM",
                    "message": f"Line {line_num}: vague term '{term}' — replace with measurable criterion",
                    "line": line_num,
                    "term": term,
                    "auto_fixable": False,
                })

    return issues


def _section_has_content(text: str) -> bool:
    """Check whether section text has real content beyond scaffolding.

    Scaffolding = blank lines, table separators, standalone table headers
    (a header row followed by a separator with no data rows).
    """
    non_blank = [ln.strip() for ln in text.splitlines() if ln.strip()]

    skip: set[int] = set()
    for i, line in enumerate(non_blank):
        if i + 1 < len(non_blank):
            nxt = non_blank[i + 1]
            is_separator = nxt.startswith("|") and set(nxt) <= {"|", "-", " ", ":"}
            is_header = line.startswith("|") and not set(line) <= {"|", "-", " ", ":"}
            if is_header and is_separator:
                skip.add(i)
                skip.add(i + 1)

    for i, line in enumerate(non_blank):
        if i in skip:
            continue
        if set(line) <= {"|", "-", " ", ":"}:
            continue
        return True

    return False


def check_sections(content: str) -> list[dict]:
    """Verify required sections exist and are non-empty."""
    issues: list[dict] = []

    for section_names in REQUIRED_SECTIONS:
        ja_name, en_name = section_names
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
            continue

        heading_level = len(match.group().split()[0])
        start = match.end()
        same_level_pattern = re.compile(r"\n#{1," + str(heading_level) + r"}\s")
        next_heading = same_level_pattern.search(content[start:])
        section_body = content[start:start + next_heading.start()] if next_heading else content[start:]

        stripped = re.sub(r"<!--.*?-->", "", section_body, flags=re.DOTALL)
        has_content = _section_has_content(stripped)
        if not has_content:
            issues.append({
                "type": "SECTION_EMPTY",
                "message": f"Section '{ja_name}' exists but has no content",
                "section": ja_name,
                "auto_fixable": False,
            })

    return issues


def check_nfr_measurable(content: str) -> list[dict]:
    """Check non-functional requirements have measurable criteria."""
    issues: list[dict] = []

    nfr_match = re.search(r"#+\s.*非機能要件", content)
    if not nfr_match:
        return issues

    nfr_start = nfr_match.end()
    next_major = re.search(r"\n##\s", content[nfr_start:])
    nfr_body = content[nfr_start:nfr_start + next_major.start()] if next_major else content[nfr_start:]

    nfr_rows = re.findall(r"\|\s*(NFR-\d+)\s*\|([^|]*)\|([^|]*)\|", nfr_body)
    for nfr_id, _, criteria in nfr_rows:
        criteria_clean = criteria.strip()
        if not criteria_clean or criteria_clean == "-":
            issues.append({
                "type": "NFR_NO_CRITERIA",
                "message": f"{nfr_id}: missing measurable criteria",
                "nfr_id": nfr_id,
                "auto_fixable": False,
            })

    return issues


def validate(doc_path: str, project_root: str, vague_terms_override: str | None = None) -> dict:
    """Run all validation checks and return structured result."""
    content = Path(doc_path).read_text(encoding="utf-8")

    if vague_terms_override:
        vague_terms = [t.strip() for t in vague_terms_override.split(",") if t.strip()]
    else:
        vague_terms = DEFAULT_VAGUE_TERMS

    all_issues: list[dict] = []
    all_issues.extend(check_req_ids(content))
    all_issues.extend(check_vague_terms(content, vague_terms))
    all_issues.extend(check_sections(content))
    all_issues.extend(check_nfr_measurable(content))

    auto_fixable = [i for i in all_issues if i.get("auto_fixable")]
    manual_fix = [i for i in all_issues if not i.get("auto_fixable")]

    req_count = len(REQ_ID_PATTERN.findall(content))

    return {
        "valid": len(all_issues) == 0,
        "total_issues": len(all_issues),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "req_count": req_count,
        "issues": all_issues,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate D-02 Requirements Specification."
    )
    parser.add_argument("document", help="Path to D-02 requirements document")
    parser.add_argument(
        "--project-root", required=True, help="Project root directory"
    )
    parser.add_argument(
        "--vague-terms", help="Comma-separated vague terms (overrides config)"
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        error = {
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-create-requirements' first to generate D-02.",
        }
        print(json.dumps(error, indent=2, ensure_ascii=False))
        sys.exit(1)

    result = validate(str(doc_path), args.project_root, args.vague_terms)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
