#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Traceability matrix coverage check (T1.5).

Reconciles the requirements (D-02) against the traceability matrix:
  - REQ defined in D-02 but with NO matrix row        (MISSING_FROM_MATRIX)
  - matrix row whose design_ref/code_ref/test_ref is  (UNTRACED_COLUMN)
    blank — present but untraced for that axis
  - REQ with no task in the task-breakdown             (REQ_WITHOUT_TASK) [--tasks]

This is the "39/39 green but 040/041/042 were never added, and stale rows trace
nothing" failure the RCA case showed. Detection only — whether a trace is
*correct* stays with the LLM/readiness layer. Exit: 0 clean, 1 gaps, 2 io error.

Run with `python` (Windows dev) or `python3` (Linux/Mac CI):
    python3 {skill-root}/scripts/check-matrix-coverage.py --d02 D-02.md --matrix matrix.md [--tasks tb.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- shared lib bootstrap (C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        REQ_ID_RE,
        matrix_coverage_gaps,
        missing_from_matrix,
        parse_matrix,
        req_num_map,
        reqs_without_task,
        verdict,
    )
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)


def check(d02_text: str, matrix_text: str, tasks_text: str | None = None) -> dict:
    issues: list[dict] = []
    # Guard the silent-green case: the matrix text has REQ ids but no parseable
    # table (unrecognized header / malformed) → coverage gaps can't be computed and
    # would falsely read clean. Surface it loudly instead.
    _, mrows = parse_matrix(matrix_text)
    if not mrows and REQ_ID_RE.search(matrix_text or ""):
        issues.append({
            "type": "NO_MATRIX_TABLE",
            "message": "matrix mentions REQ ids but no parseable table was found "
                       "(unrecognized header columns or malformed table)",
            "auto_fixable": False,
        })
    for rid in missing_from_matrix(d02_text, matrix_text):
        issues.append({
            "type": "MISSING_FROM_MATRIX",
            "message": f"{rid} is defined in D-02 but has no matrix row",
            "req_id": rid, "auto_fixable": False,
        })
    for rid, empty in matrix_coverage_gaps(matrix_text).items():
        issues.append({
            "type": "UNTRACED_COLUMN",
            "message": f"{rid}: empty trace column(s): {', '.join(empty)}",
            "req_id": rid, "columns": empty, "auto_fixable": False,
        })
    checked = ["REQ defined in D-02 has a matrix row",
               "matrix rows trace design_ref/code_ref/test_ref"]
    if tasks_text is not None:
        d02_reqs = list(req_num_map(d02_text)[0].values())
        for rid in reqs_without_task(d02_reqs, tasks_text):
            issues.append({
                "type": "REQ_WITHOUT_TASK",
                "message": f"{rid} has no task in the task-breakdown",
                "req_id": rid, "auto_fixable": False,
            })
        checked.append("every REQ has ≥1 task in the task-breakdown")

    _, slugs = req_num_map(d02_text)
    structure_ok = not issues
    v = verdict(structure_ok, semantic_review=SEMANTIC_NA, checked=checked,
                not_checked=["whether each trace is semantically correct (LLM / readiness)"])
    v.update({"valid": structure_ok, "total_issues": len(issues), "issues": issues})
    if len(slugs) > 1:
        v["multi_feature_warning"] = (
            f"multiple feature slugs detected ({sorted(slugs)}); trailing-number "
            "identity may collide — counts unreliable"
        )
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description="Traceability matrix coverage check (T1.5).")
    ap.add_argument("--d02", required=True, help="Path to D-02 requirements")
    ap.add_argument("--matrix", required=True, help="Path to traceability matrix")
    ap.add_argument("--tasks", help="Path to task-breakdown (enables REQ_WITHOUT_TASK)")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    try:
        d02 = Path(args.d02).read_text(encoding="utf-8")
        matrix = Path(args.matrix).read_text(encoding="utf-8")
        tasks = Path(args.tasks).read_text(encoding="utf-8") if args.tasks else None
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"error": f"not readable: {exc}", "valid": False}, ensure_ascii=False))
        return 2

    result = check(d02, matrix, tasks)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write {args.output}: {exc}", "valid": False}, ensure_ascii=False))
            return 2
    else:
        print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
