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
import glob
import json
import re
import sys

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

# Feature-namespaced REQ ids (REQ-<FEAT>-NNN / REQ-SHARED-NNN); tolerant of legacy REQ-NNN.
REQ_ID_RE = re.compile(r"REQ-(?:[A-Z0-9]+(?:-[A-Z0-9]+)*-)?\d{3,}")
COLUMNS = ["feature", "req_id", "story_id", "design_ref", "code_ref", "test_ref", "gate_status", "timestamp"]
COVERAGE_COLUMNS = ["design_ref", "code_ref", "test_ref"]


def parse_matrix(matrix_path: str) -> list[dict]:
    """Parse markdown table rows into matrix entries.

    Header-aware: the column order is taken from the detected header row, so the
    skill parses both the v2 8-column matrix (leading `feature` column) and a
    legacy 7-column matrix (no `feature`) correctly. Without this, a fixed
    positional map against the 8-column COLUMNS would shift every cell by one in a
    legacy matrix (feature←req_id, design_ref←story_id, …) and miscount coverage.
    """
    text = Path(matrix_path).read_text(encoding="utf-8")
    lines = text.strip().splitlines()

    rows: list[dict] = []
    in_table = False
    col_order: list[str] = COLUMNS  # fallback if no header row is seen

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
            if cells[0].lower() in ("feature", "req_id"):
                in_table = True
                # Capture the actual header so data rows map by name, not position.
                col_order = [c.strip().lower() for c in cells]
            continue

        row: dict = {col: "" for col in COLUMNS}
        for i, cell in enumerate(cells):
            if i < len(col_order):
                key = col_order[i]
                if key in COLUMNS:
                    row[key] = cell.strip()
        # Raw parsed cell count (every row is pre-filled with all COLUMNS keys, so
        # a `col in row` test can't detect a truncated row — validate_matrix uses
        # this against the table's own header width instead).
        row["_raw_cols"] = len(cells)
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

    # Compare each row's raw cell count against the table's own width (the widest
    # row = its header), so a truncated row is caught WITHOUT penalizing a
    # consistent legacy 7-column matrix.
    widths = [r.get("_raw_cols", 0) for r in rows]
    width = max(widths) if widths else 0
    for i, r in enumerate(rows, 1):
        raw = r.get("_raw_cols", width)
        if raw < width:
            issues.append(f"Row {i} has {raw}/{width} columns")

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


def _is_shared(row: dict) -> bool:
    """A shared-scope matrix row (feature column == 'shared', case-insensitive).
    Shared REQs (REQ-SHARED-NNN) are referenced in EVERY feature's matrix, so they
    must be counted once at roll-up — not once per feature — and kept out of each
    feature's own coverage denominator so they neither inflate nor dilute it."""
    return row.get("feature", "").strip().lower() == "shared"


def rollup(pattern: str, out_path: str | None) -> dict:
    """Aggregate coverage across per-feature matrices (TRR cross-feature roll-up).

    Per-feature totals count that feature's OWN rows only (shared rows excluded).
    Shared rows are deduped by req_id across all matrices and reported in their own
    bucket; a shared REQ counts as fully traced only if it is fully traced in every
    matrix that references it. Grand totals = sum(feature-specific) + unique shared,
    so a shared REQ is never double-counted across features.
    """
    paths = sorted(glob.glob(pattern, recursive=True))
    features: list[dict] = []
    g_total = g_traced = 0
    shared_seen: dict[str, bool] = {}  # req_id -> fully traced wherever it appears
    for p in paths:
        rows = parse_matrix(p)
        feat_rows = [r for r in rows if not _is_shared(r)]
        rep = generate_report(feat_rows)
        parts = Path(p).parts
        feat = parts[parts.index("features") + 1] if "features" in parts else Path(p).stem
        features.append({
            "feature": feat,
            "total": rep["total_requirements"],
            "fully_traced": rep["fully_traced"],
            "pct": rep["fully_traced_pct"],
        })
        g_total += rep["total_requirements"]
        g_traced += rep["fully_traced"]
        for r in rows:
            if not _is_shared(r):
                continue
            rid = r.get("req_id", "")
            if not rid:
                continue
            traced = all(r.get(col) for col in COVERAGE_COLUMNS)
            shared_seen[rid] = (shared_seen[rid] and traced) if rid in shared_seen else traced

    shared_total = len(shared_seen)
    shared_traced = sum(1 for v in shared_seen.values() if v)
    shared_pct = round(shared_traced / shared_total * 100, 1) if shared_total else 0.0
    grand_total = g_total + shared_total
    grand_traced = g_traced + shared_traced
    g_pct = round(grand_traced / grand_total * 100, 1) if grand_total else 0.0
    result = {
        "features": features,
        "shared": {"total": shared_total, "fully_traced": shared_traced, "pct": shared_pct},
        "grand_total": grand_total,
        "grand_fully_traced": grand_traced,
        "grand_pct": g_pct,
        "matrices_found": len(paths),
    }
    if out_path:
        lines = [
            "# Traceability Coverage Roll-up",
            "",
            "| feature | total | fully traced | % |",
            "|---|---|---|---|",
        ]
        for f in features:
            lines.append(f"| {f['feature']} | {f['total']} | {f['fully_traced']} | {f['pct']} |")
        if shared_total:
            lines.append(f"| _shared_ | {shared_total} | {shared_traced} | {shared_pct} |")
        lines.append(f"| **TOTAL** | **{grand_total}** | **{grand_traced}** | **{g_pct}** |")
        op = Path(out_path)
        op.parent.mkdir(parents=True, exist_ok=True)
        op.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate traceability coverage report from matrix."
    )
    parser.add_argument(
        "--matrix", help="Path to traceability matrix markdown (per-feature)"
    )
    parser.add_argument(
        "--rollup", help="Glob of per-feature matrices to aggregate cross-feature",
    )
    parser.add_argument(
        "--out", help="Output markdown path for the --rollup report",
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

    if args.rollup:
        result = rollup(args.rollup, args.out)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0)

    if not args.matrix:
        print(json.dumps({"error": "Either --matrix or --rollup is required"}, ensure_ascii=False))
        sys.exit(2)

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
