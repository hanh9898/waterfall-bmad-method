#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-03 Glossary document.

Checks for duplicate terms, empty definitions, minimum term count, and required
sections (English canonical + configured document language — NO hardcoded
Japanese). Returns a structured JSON honest verdict
(structure_ok / semantic_review / checked / not_checked).

Shares table/section/verdict primitives with the HBC validation library.
"""

import argparse
import json
import sys
from pathlib import Path

# --- shared lib bootstrap (Đợt 0 / C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
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

# (English canonical, configured-language label). English is reported in issues;
# either label satisfies the presence check. No Japanese.
REQUIRED_SECTIONS = [
    ("Terms", "Thuật ngữ"),
    ("Abbreviations", "Từ viết tắt"),
    ("Revision History", "Lịch sử sửa đổi"),
]

TERMS_LABELS = ("Terms", "Thuật ngữ")
ABBREV_LABELS = ("Abbreviations", "Từ viết tắt")


def _rows_to_entries(rows: list[list[str]]) -> list[dict]:
    """Map raw table rows to {term, definition}, skipping rows with empty term."""
    entries: list[dict] = []
    for cells in rows:
        if not cells or not cells[0]:
            continue
        entries.append({
            "term": cells[0],
            "definition": cells[1] if len(cells) > 1 else "",
        })
    return entries


def check_duplicates(terms_rows: list[dict], abbrev_rows: list[dict]) -> list[dict]:
    """Check for duplicate terms across both tables."""
    issues: list[dict] = []
    all_terms: dict[str, int] = {}

    for row in terms_rows + abbrev_rows:
        term_lower = row["term"].lower()
        if term_lower in all_terms:
            issues.append({
                "type": "DUPLICATE_TERM",
                "message": f"Duplicate term: '{row['term']}'",
                "term": row["term"],
                "auto_fixable": True,
            })
        else:
            all_terms[term_lower] = 1

    return issues


def check_empty_definitions(terms_rows: list[dict], abbrev_rows: list[dict]) -> list[dict]:
    """Check for terms with empty definitions."""
    issues: list[dict] = []

    for row in terms_rows:
        if not row["definition"].strip() or row["definition"].strip() == "-":
            issues.append({
                "type": "EMPTY_DEFINITION",
                "message": f"Term '{row['term']}' has no definition",
                "term": row["term"],
                "auto_fixable": False,
            })

    for row in abbrev_rows:
        if not row["definition"].strip() or row["definition"].strip() == "-":
            issues.append({
                "type": "EMPTY_DEFINITION",
                "message": f"Abbreviation '{row['term']}' has no definition",
                "term": row["term"],
                "auto_fixable": False,
            })

    return issues


def check_sections(content: str) -> list[dict]:
    """Verify required sections exist (English or configured label)."""
    issues: list[dict] = []

    for en_name, lang_name in REQUIRED_SECTIONS:
        if not find_section(content, en_name, lang_name):
            issues.append({
                "type": "SECTION_MISSING",
                "message": f"Required section '{en_name}' / '{lang_name}' not found",
                "section": en_name,
                "auto_fixable": False,
            })

    return issues


CHECKED = [
    "required sections present",
    "duplicate terms across tables",
    "empty definitions",
    "minimum term count",
]
NOT_CHECKED = [
    "definition quality / accuracy (LLM review)",
    "domain term completeness (LLM review)",
    "consistency with D-02 term usage (readiness gate)",
]


def validate(doc_path: str) -> dict:
    """Run all structural validation checks and return the honest verdict."""
    content = Path(doc_path).read_text(encoding="utf-8")

    terms_rows = _rows_to_entries(parse_table(content, *TERMS_LABELS))
    abbrev_rows = _rows_to_entries(parse_table(content, *ABBREV_LABELS))

    all_issues: list[dict] = []
    all_issues.extend(check_sections(content))
    all_issues.extend(check_duplicates(terms_rows, abbrev_rows))
    all_issues.extend(check_empty_definitions(terms_rows, abbrev_rows))

    total_terms = len(terms_rows) + len(abbrev_rows)
    if total_terms == 0:
        all_issues.append({
            "type": "NO_TERMS",
            "message": "Glossary contains no terms",
            "auto_fixable": False,
        })

    auto_fixable = [i for i in all_issues if i.get("auto_fixable")]
    manual_fix = [i for i in all_issues if not i.get("auto_fixable")]

    structure_ok = len(all_issues) == 0
    result = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=CHECKED,
        not_checked=NOT_CHECKED,
    )
    result.update({
        "valid": structure_ok,
        "total_issues": len(all_issues),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "term_count": len(terms_rows),
        "abbreviation_count": len(abbrev_rows),
        "total_entries": total_terms,
        "issues": all_issues,
    })
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Validate D-03 Glossary document."
    )
    parser.add_argument("document", help="Path to D-03 glossary document")
    parser.add_argument(
        "--project-root", required=True, help="Project root directory"
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    doc_path = Path(args.document)
    if not doc_path.exists():
        error = {
            "error": f"Document not found: {args.document}",
            "suggestion": "Run 'hbc-create-glossary' first to generate D-03.",
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
