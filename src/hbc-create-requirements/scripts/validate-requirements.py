#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-02 Requirements Specification document.

Checks REQ ID uniqueness and sequencing (counted ONLY from the functional
requirements table's ID column — not prose references), flags vague terms,
verifies required sections are present and non-empty (English canonical +
configured document language, no hardcoded Japanese), and returns a structured
JSON honest verdict (structure_ok / semantic_review / checked / not_checked).

Shares table/section/verdict primitives with the HBC validation library.
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
        find_section,
        parse_table,
        section_body,
        verdict,
    )
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install the hbc-shared component alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

# Each entry: (English canonical, configured-language label). The English label
# is reported in issues; either label satisfies the presence check. No Japanese.
REQUIRED_SECTIONS = [
    ("Project Overview", "Tổng quan dự án"),
    ("Scope", "Phạm vi"),
    ("User Roles", "Vai trò người dùng"),
    ("Functional Requirements", "Yêu cầu chức năng"),
    ("Non-Functional Requirements", "Yêu cầu phi chức năng"),
    ("Constraints", "Ràng buộc"),
]

DEFAULT_VAGUE_TERMS = [
    "fast", "easy", "user-friendly", "simple", "good",
    "nice", "efficient", "appropriate", "adequate", "reasonable",
]

REQ_ID_PATTERN = re.compile(r"REQ-(\d{3,})")


def functional_req_ids(content: str) -> list[str]:
    """REQ ID numbers defined in the functional requirements table.

    Takes the first REQ-xxx found in each table row (the row's own ID column,
    wherever it sits — tolerates a leading "No." column). Prose references
    outside the table are never seen, so they cannot inflate counts (S-4).
    """
    rows = parse_table(content, "Functional Requirements", "Yêu cầu chức năng")
    ids: list[str] = []
    for cells in rows:
        for cell in cells:
            # Anchored match: the cell must BE a REQ id (the ID column), not merely
            # contain one — so a prose reference like "See REQ-001" in another cell
            # of an id-less row does not produce a ghost/duplicate id (F7).
            m = REQ_ID_PATTERN.match(cell.strip())
            if m:
                ids.append(m.group(1))
                break  # one ID per row
    return ids


def check_req_ids(content: str) -> list[dict]:
    """Validate REQ IDs are unique and sequential.

    Definitions are taken ONLY from the functional requirements table — a
    REQ-xxx mentioned in prose (User Roles, Assumptions, Acceptance Criteria,
    etc.) is a reference, not a definition, and must not trigger duplicate/order
    issues (S-4).
    """
    issues: list[dict] = []

    matches = functional_req_ids(content)

    if not matches:
        issues.append({
            "type": "REQ_ID_MISSING",
            "message": "No REQ-xxx IDs found in the functional requirements table",
            "auto_fixable": False,
        })
        return issues

    ids = [int(m) for m in matches]
    seen: dict[int, int] = {}
    for i, req_num in enumerate(ids, 1):
        if req_num in seen:
            issues.append({
                "type": "REQ_ID_DUPLICATE",
                "message": f"REQ-{req_num:03d} appears at table positions {seen[req_num]} and {i}",
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
            "message": "REQ IDs are not in ascending order in the functional table",
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


def check_sections(content: str) -> list[dict]:
    """Required sections present + non-empty (shared lib; English or VN label).

    F9: was a bespoke copy of the section/empty logic; now delegates to the shared
    `check_required_sections` like every other validator (removes drift).
    """
    return check_required_sections(content, REQUIRED_SECTIONS)


def check_nfr_measurable(content: str) -> list[dict]:
    """Check non-functional requirements have measurable criteria."""
    issues: list[dict] = []

    nfr_match = find_section(content, "Non-Functional Requirements", "Yêu cầu phi chức năng")
    if not nfr_match:
        return issues

    nfr_body = section_body(content, nfr_match)
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


# Structural checks this validator performs, and the semantic facets it
# deliberately does NOT judge (deferred to the LLM review layer — Đợt 2).
CHECKED = [
    "REQ ID uniqueness/sequence (functional table column)",
    "vague terminology",
    "required sections present and non-empty",
    "NFR measurable-criteria presence",
]
NOT_CHECKED = [
    "REQ semantic correctness / đủ-nghĩa (LLM review)",
    "REQ facet coverage: read/write · api/admin (LLM review)",
    "cross-document consistency D-02 ↔ D-03/D-06/... (readiness gate)",
]


def validate(doc_path: str, project_root: str, vague_terms_override: str | None = None) -> dict:
    """Run all structural validation checks and return the honest verdict."""
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

    req_count = len(functional_req_ids(content))

    structure_ok = len(all_issues) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=CHECKED,
        not_checked=NOT_CHECKED,
    )
    # Backward-compatible keys (consumed by SKILL.md / phase-gate) + new verdict fields.
    result.update({
        "valid": structure_ok,
        "total_issues": len(all_issues),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "req_count": req_count,
        "issues": all_issues,
    })
    return result


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
