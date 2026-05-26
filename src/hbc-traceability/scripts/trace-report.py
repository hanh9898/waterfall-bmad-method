#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Parse a traceability matrix markdown table and generate coverage statistics.

Reads the living matrix file, counts filled vs empty cells per column,
identifies gaps, and returns structured JSON for the Report and Audit
capabilities of hbc-traceability.
"""

import argparse
import json
import sys
from pathlib import Path

COLUMNS = ["req_id", "story_id", "design_ref", "code_ref", "test_ref", "gate_status", "timestamp"]
COVERAGE_COLUMNS = ["design_ref", "code_ref", "test_ref"]


def parse_matrix(matrix_path: str) -> list[dict]:
    """Parse markdown table rows into matrix entries."""
    text = Path(matrix_path).read_text(encoding="utf-8")
    lines = text.strip().splitlines()

    rows: list[dict] = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            in_table = False
            continue

        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 2:
            continue

        if set(cells[0]) <= {"-", " "}:
            in_table = True
            continue

        if not in_table:
            if cells[0].lower() == "req_id":
                in_table = True
            continue

        row: dict = {}
        for i, col in enumerate(COLUMNS):
            row[col] = cells[i].strip() if i < len(cells) and cells[i].strip() else ""
        rows.append(row)

    return rows


def generate_report(rows: list[dict]) -> dict:
    """Generate coverage statistics from parsed matrix rows."""
    total = len(rows)
    if total == 0:
        return {
            "total_requirements": 0,
            "coverage": {col: 0 for col in COVERAGE_COLUMNS},
            "fully_traced": 0,
            "fully_traced_pct": 0.0,
            "gaps": [],
            "gap_details": [],
        }

    coverage = {}
    for col in COVERAGE_COLUMNS:
        coverage[col] = sum(1 for r in rows if r.get(col))

    fully_traced = sum(
        1 for r in rows
        if all(r.get(col) for col in COVERAGE_COLUMNS)
    )

    gaps: list[str] = []
    gap_details: list[dict] = []
    for r in rows:
        missing = [col for col in COVERAGE_COLUMNS if not r.get(col)]
        if missing:
            req_id = r.get("req_id", "UNKNOWN")
            gaps.append(req_id)
            gap_details.append({
                "req_id": req_id,
                "missing_columns": missing,
            })

    return {
        "total_requirements": total,
        "coverage": coverage,
        "fully_traced": fully_traced,
        "fully_traced_pct": round(fully_traced / total * 100, 1) if total else 0.0,
        "gaps": gaps,
        "gap_details": gap_details,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate traceability coverage report from matrix."
    )
    parser.add_argument(
        "--matrix", required=True, help="Path to traceability matrix markdown"
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    matrix_path = Path(args.matrix)
    if not matrix_path.exists():
        error = {
            "error": f"Matrix file not found: {args.matrix}",
            "suggestion": "Run 'traceability init' first to create the matrix.",
        }
        print(json.dumps(error, indent=2, ensure_ascii=False))
        sys.exit(1)

    rows = parse_matrix(str(matrix_path))
    report = generate_report(rows)

    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    sys.exit(0 if not report["gaps"] else 1)


if __name__ == "__main__":
    main()
