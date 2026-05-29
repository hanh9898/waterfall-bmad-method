#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate a D-03 Glossary document.

Checks for duplicate terms, empty definitions, minimum term count,
and structural integrity. Returns structured JSON with per-issue
auto_fixable flag.
"""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "用語一覧",
    "略語一覧",
    "改訂履歴",
]


def parse_table_rows(content: str, section_name: str) -> list[dict]:
    """Extract data rows from a markdown table under a section heading."""
    pattern = re.compile(rf"#+\s.*{re.escape(section_name)}.*", re.IGNORECASE)
    match = pattern.search(content)
    if not match:
        return []

    start = match.end()
    next_heading = re.search(r"\n##\s", content[start:])
    section_body = content[start:start + next_heading.start()] if next_heading else content[start:]

    rows: list[dict] = []
    in_table = False

    for line in section_body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 2:
            continue

        if set(cells[0]) <= {"-", " ", ":"}:
            in_table = True
            continue

        if not in_table:
            in_table = True
            continue

        if cells[0]:
            rows.append({"term": cells[0], "definition": cells[1] if len(cells) > 1 else ""})

    return rows


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
    """Verify required sections exist."""
    issues: list[dict] = []

    for section in REQUIRED_SECTIONS:
        pattern = re.compile(rf"#+\s.*{re.escape(section)}.*", re.IGNORECASE)
        if not pattern.search(content):
            issues.append({
                "type": "SECTION_MISSING",
                "message": f"Required section '{section}' not found",
                "section": section,
                "auto_fixable": False,
            })

    return issues


def validate(doc_path: str) -> dict:
    """Run all validation checks and return structured result."""
    content = Path(doc_path).read_text(encoding="utf-8")

    terms_rows = parse_table_rows(content, "用語一覧")
    abbrev_rows = parse_table_rows(content, "略語一覧")

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

    return {
        "valid": len(all_issues) == 0,
        "total_issues": len(all_issues),
        "auto_fixable_count": len(auto_fixable),
        "manual_fix_count": len(manual_fix),
        "term_count": len(terms_rows),
        "abbreviation_count": len(abbrev_rows),
        "total_entries": total_terms,
        "issues": all_issues,
    }


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
