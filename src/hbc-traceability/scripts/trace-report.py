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
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

REQ_ID_RE = re.compile(r"REQ-\d{3,}")
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


def detect_phase(rows: list[dict]) -> dict:
    """Determine which phase update is needed from empty column analysis."""
    total = len(rows)
    if total == 0:
        return {"next_phase": 1, "empty_columns": COVERAGE_COLUMNS, "total_rows": 0}

    empty_cols = [
        col for col in COVERAGE_COLUMNS
        if all(not r.get(col) for r in rows)
    ]

    phase_map = {"design_ref": 2, "code_ref": 3, "test_ref": 4}
    next_phase = min((phase_map[col] for col in empty_cols), default=0)

    return {
        "next_phase": next_phase,
        "empty_columns": empty_cols,
        "total_rows": total,
    }


def validate_matrix(rows: list[dict]) -> dict:
    """Validate matrix structural integrity."""
    issues: list[str] = []

    req_ids = [r.get("req_id", "") for r in rows]
    empty_ids = [i for i, rid in enumerate(req_ids, 1) if not rid]
    if empty_ids:
        issues.append(f"Empty req_id in row(s): {empty_ids}")

    seen: dict[str, int] = {}
    for i, rid in enumerate(req_ids, 1):
        if rid and rid in seen:
            issues.append(f"Duplicate req_id '{rid}' in rows {seen[rid]} and {i}")
        elif rid:
            seen[rid] = i

    for i, r in enumerate(rows, 1):
        col_count = sum(1 for c in COLUMNS if c in r)
        if col_count < len(COLUMNS):
            issues.append(f"Row {i} has {col_count}/{len(COLUMNS)} columns")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "rows_checked": len(rows),
    }


def _d02_req_ids(text: str) -> set[str]:
    """REQ ids DEFINED in D-02 — taken from the functional requirements table's ID
    column only, NOT prose references (mirrors the S-4 fix; F2). Falls back to a
    whole-file scan if the shared lib is unavailable."""
    labels = ("Functional Requirements", "Yêu cầu chức năng")
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
        from hbc_validation import find_section, parse_table  # noqa: E402
        if find_section(text, *labels):
            # Section present → its table's ID column is authoritative, even when
            # empty (a draft with no rows means "no REQ defined yet"). Do NOT fall
            # back to a whole-file scan here, or prose refs leak back in (F2).
            ids: set[str] = set()
            for cells in parse_table(text, *labels):
                for cell in cells:
                    m = REQ_ID_RE.match(cell.strip())
                    if m:
                        ids.add(m.group(0))
                        break
            return ids
    except Exception:
        pass
    # Only reached when the functional section is absent (non-standard D-02) or
    # the shared lib is unavailable — best-effort whole-file scan.
    return set(REQ_ID_RE.findall(text))


def sync_with_d02(rows: list[dict], d02_path: str) -> dict:
    """Cross-check matrix REQ ids against D-02 (A-4).

    Closes the gap where the traceability audit only checked the matrix
    internally and never compared it to the authoritative requirement source.
    `orphan_in_matrix` = traced but not defined in D-02; `missing_from_matrix`
    = defined in D-02 but never traced.
    """
    try:
        text = Path(d02_path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"error": f"D-02 not readable: {d02_path}", "in_sync": False}
    d02_ids = _d02_req_ids(text)
    matrix_ids = {r["req_id"] for r in rows if r.get("req_id")}
    orphan = sorted(matrix_ids - d02_ids)
    missing = sorted(d02_ids - matrix_ids)
    return {
        "in_sync": not orphan and not missing,
        "d02_req_count": len(d02_ids),
        "matrix_req_count": len(matrix_ids),
        "orphan_in_matrix": orphan,
        "missing_from_matrix": missing,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate traceability coverage report from matrix."
    )
    parser.add_argument(
        "--matrix", required=True, help="Path to traceability matrix markdown"
    )
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit 1 when gaps exist (default: exit 0 on successful parse)",
    )
    parser.add_argument(
        "--detect-phase", action="store_true",
        help="Return compact phase detection instead of full report",
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate matrix structure (column count, duplicate/empty req_ids)",
    )
    parser.add_argument(
        "--d02", help="Path to D-02 — cross-check matrix REQ ids vs D-02 (A-4)",
    )
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

    if args.validate:
        result = validate_matrix(rows)
    elif args.detect_phase:
        result = detect_phase(rows)
    else:
        result = generate_report(rows)

    d02_in_sync = True
    if args.d02 and not args.detect_phase:
        sync = sync_with_d02(rows, args.d02)
        result["d02_sync"] = sync
        d02_in_sync = sync.get("in_sync", False)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    if args.validate:
        sys.exit(0 if result.get("valid") and d02_in_sync else 1)
    if args.detect_phase:
        sys.exit(0)
    sys.exit(1 if (args.strict and (result.get("gaps") or not d02_in_sync)) else 0)


if __name__ == "__main__":
    main()
