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

# --- shared lib bootstrap (Batch 0 / C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        check_required_sections,
        parse_table,
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

# group1 = namespace (feature/SHARED, e.g. AUTH); group2 = number. Legacy REQ-NNN → ns "".
REQ_ID_PATTERN = re.compile(r"REQ-(?:([A-Z0-9]+(?:-[A-Z0-9]+)*)-)?(\d{3,})")

# Namespace-aware NFR id (full-match a single cell): NFR-001 / NFR-AUTH-001 / NFR-SHARED-001.
NFR_ID_RE = re.compile(r"NFR-(?:[A-Z0-9]+(?:-[A-Z0-9]+)*-)?\d{3,}")


def functional_req_rows(content: str) -> list[list[str]]:
    """Rows (cell-lists) of the functional requirements table."""
    return parse_table(content, "Functional Requirements", "Yêu cầu chức năng")


def functional_req_ids(content: str) -> list[tuple[str, int]]:
    """(namespace, number) for each REQ id in the functional table's ID column.

    namespace = feature/SHARED prefix (e.g. 'AUTH'); '' for legacy REQ-NNN.
    Anchored match on the ID cell (prose refs elsewhere ignored — S-4/F7).
    """
    out: list[tuple[str, int]] = []
    for cells in functional_req_rows(content):
        for cell in cells:
            m = REQ_ID_PATTERN.match(cell.strip())
            if m:
                out.append((m.group(1) or "", int(m.group(2))))
                break  # one ID per row
    return out


def _fmt(ns: str, num: int) -> str:
    return f"REQ-{ns + '-' if ns else ''}{num:03d}"


def check_req_ids(content: str) -> list[dict]:
    """Validate REQ IDs: unique + sequential WITHIN each namespace (feature/SHARED).

    Gaps BETWEEN namespaces are fine (different features). Within a namespace,
    numbers must be unique and gap-free (1..max). Definitions taken ONLY from the
    functional table (prose refs are references, not definitions — S-4).
    """
    issues: list[dict] = []
    entries = functional_req_ids(content)

    if not entries:
        issues.append({
            "type": "REQ_ID_MISSING",
            "message": "No REQ-xxx IDs found in the functional requirements table",
            "auto_fixable": False,
        })
        return issues

    by_ns: dict[str, list[int]] = {}
    for ns, num in entries:
        by_ns.setdefault(ns, []).append(num)

    for ns, nums in by_ns.items():
        seen: dict[int, int] = {}
        for i, n in enumerate(nums, 1):
            if n in seen:
                issues.append({
                    "type": "REQ_ID_DUPLICATE",
                    "message": f"{_fmt(ns, n)} appears at positions {seen[n]} and {i}",
                    "auto_fixable": True,
                    "req_id": _fmt(ns, n),
                })
            else:
                seen[n] = i

        missing = [n for n in range(1, max(nums) + 1) if n not in set(nums)]
        if missing:
            issues.append({
                "type": "REQ_ID_GAP",
                "message": f"Namespace {ns or '(legacy)'}: missing {', '.join(_fmt(ns, n) for n in missing)}",
                "auto_fixable": True,
                "missing_ids": [_fmt(ns, n) for n in missing],
            })

        if nums != sorted(nums):
            issues.append({
                "type": "REQ_ID_ORDER",
                "message": f"Namespace {ns or '(legacy)'}: REQ IDs not in ascending order",
                "auto_fixable": True,
            })

    return issues


def check_ears(content: str) -> list[dict]:
    """ADVISORY (cluster 7=A): each functional requirement should follow EARS —
    English keyword 'SHALL' (e.g. 'WHEN <condition> THE SYSTEM SHALL <behavior>').
    WARNING only, does NOT fail structure_ok."""
    issues: list[dict] = []
    for cells in functional_req_rows(content):
        rid = ""
        for c in cells:
            if REQ_ID_PATTERN.match(c.strip()):
                rid = c.strip()
                break
        if rid and "shall" not in " ".join(cells).lower():
            issues.append({
                "type": "EARS_ADVISORY",
                "message": f"{rid}: not in EARS form (missing 'SHALL'). Suggestion: 'WHEN <condition> THE SYSTEM SHALL <behavior>'.",
                "auto_fixable": False,
                "advisory": True,
                "req_id": rid,
            })
    return issues


def check_vague_terms(content: str, vague_terms: list[str]) -> list[dict]:
    """Flag vague terms in requirement descriptions.

    Skips the YAML frontmatter and fenced code blocks: a vague word in
    ``title: "A simple test"`` or inside a code example is not a requirement defect
    and would otherwise produce a blocking false-fail. Line numbers are kept
    accurate by masking those line ranges in place rather than removing them.
    """
    issues: list[dict] = []
    lines = content.splitlines()

    in_frontmatter = False
    in_fence = False
    fence_char: str | None = None

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # YAML frontmatter delimited by `---` at the very top of the file.
        if line_num == 1 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if stripped == "---":
                in_frontmatter = False
            continue

        # Fenced code blocks (``` or ~~~) — content inside is not requirement text.
        fence = re.match(r"^[ \t]*(`{3,}|~{3,})", line)
        if not in_fence:
            if fence:
                in_fence = True
                fence_char = fence.group(1)[0]
                continue
        else:
            if fence and fence.group(1)[0] == fence_char:
                in_fence = False
            continue

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
    """Check non-functional requirements have measurable criteria.

    Parses the NFR section's table(s) via the shared parse_table (language-aware,
    header/separator excluded, multi-sub-table aware) instead of a bespoke
    3-column regex. The measurable criteria is the LAST column, so the check holds
    regardless of how many columns the table has; the NFR id is matched with a
    namespace-aware pattern so NFR-AUTH-001 / NFR-SHARED-001 are not skipped.
    """
    issues: list[dict] = []

    rows = parse_table(content, "Non-Functional Requirements", "Yêu cầu phi chức năng")
    for cells in rows:
        nfr_id = next((c.strip() for c in cells if NFR_ID_RE.fullmatch(c.strip())), None)
        if not nfr_id:
            continue
        criteria_clean = cells[-1].strip()
        if not criteria_clean or criteria_clean == "-":
            issues.append({
                "type": "NFR_NO_CRITERIA",
                "message": f"{nfr_id}: missing measurable criteria",
                "nfr_id": nfr_id,
                "auto_fixable": False,
            })

    return issues


# Structural checks this validator performs, and the semantic facets it
# deliberately does NOT judge (deferred to the LLM review layer — Batch 2).
CHECKED = [
    "REQ ID uniqueness/sequence per namespace (feature/SHARED)",
    "vague terminology",
    "required sections present and non-empty",
    "NFR measurable-criteria presence",
    "EARS shape (advisory — warning only, does not fail)",
]
NOT_CHECKED = [
    "REQ semantic correctness / completeness (LLM review)",
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
    all_issues.extend(check_ears(content))

    # Advisory issues (EARS) warn but do NOT fail the structural verdict (cluster 7=A).
    blocking = [i for i in all_issues if not i.get("advisory")]
    advisory = [i for i in all_issues if i.get("advisory")]
    auto_fixable = [i for i in blocking if i.get("auto_fixable")]
    manual_fix = [i for i in blocking if not i.get("auto_fixable")]

    req_count = len(functional_req_ids(content))

    structure_ok = len(blocking) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=CHECKED,
        not_checked=NOT_CHECKED,
    )
    # Backward-compatible keys (consumed by SKILL.md / phase-gate) + new verdict fields.
    result.update({
        "valid": structure_ok,
        "total_issues": len(blocking),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "advisory_count": len(advisory),
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
