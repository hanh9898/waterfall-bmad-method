#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Validate Phase 3 implementation reality (D2).

Reconciles the task breakdown and the traceability matrix against the code on
disk — closing the seam where a task is marked DONE with no test assigned, or the
matrix points `code_ref` at files that do not exist, which lets "implementation
complete" pass with nothing actually behind it.

Checks:
  - DONE task with no test_refs                      (DONE_TASK_NO_TEST)
  - matrix code_ref pointing at a non-existent file  (MISSING_CODE_FILE)   [--matrix]
  - matrix REQ designed + tested but code_ref empty  (REQ_NOT_IMPLEMENTED) [--matrix]

Deterministic structural reconciliation only — whether the code actually fulfils
the task stays with the LLM review layer / acceptance. Exit: 0 clean, 1 gaps,
2 arg/io error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- shared lib bootstrap (C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import SEMANTIC_NA, verdict  # noqa: E402
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

# task table: | task_id | description | design_ref | test_refs | priority | status | dependencies |
_TASK_ROW_RE = re.compile(
    r"\|\s*(TASK-\d{3,})\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|"
)
_EMPTY = {"", "-", "n/a", "none", "tbd"}


def _blank(cell: str) -> bool:
    return cell.strip().lower() in _EMPTY


def check_done_tasks(tasks_text: str) -> list[dict]:
    """A task marked DONE must have at least one assigned test (test_refs) — a DONE
    task with no test is work claimed complete with nothing verifying it."""
    issues: list[dict] = []
    for m in _TASK_ROW_RE.finditer(tasks_text):
        task_id, _desc, _design, test_refs, _prio, status, _deps = (g.strip() for g in m.groups())
        if status.lower() == "done" and _blank(test_refs):
            issues.append({
                "type": "DONE_TASK_NO_TEST",
                "message": f"{task_id} is DONE but has no test_refs (no test case assigned)",
                "task_id": task_id,
                "auto_fixable": False,
            })
    return issues


def _matrix_rows(matrix_text: str) -> list[list[str]]:
    """Data rows of the traceability matrix
    (req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp)."""
    rows: list[list[str]] = []
    for line in matrix_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if joined and set(joined) <= {"-", " ", ":"}:
            continue  # separator
        if not re.match(r"REQ-\d{3,}", cells[0]):
            continue  # header / non-data row — only REQ-keyed rows count
        rows.append(cells)
    return rows


def check_matrix(matrix_text: str, project_root: str) -> list[dict]:
    issues: list[dict] = []
    for cells in _matrix_rows(matrix_text):
        req_id = cells[0]
        design_ref = cells[2] if len(cells) > 2 else ""
        code_ref = cells[3] if len(cells) > 3 else ""
        test_ref = cells[4] if len(cells) > 4 else ""

        # code_ref tokens that look like file paths must exist on disk.
        if not _blank(code_ref):
            for tok in re.split(r"[,\s]+", code_ref):
                tok = tok.strip().strip("`")
                if not tok or _blank(tok):
                    continue
                if "/" in tok or re.search(r"\.\w+$", tok):  # looks like a path
                    p = Path(tok) if Path(tok).is_absolute() else Path(project_root) / tok
                    if not p.exists():
                        issues.append({
                            "type": "MISSING_CODE_FILE",
                            "message": f"{req_id}: code_ref '{tok}' does not exist on disk",
                            "req_id": req_id,
                            "path": tok,
                            "auto_fixable": False,
                        })

        # designed + tested but no code linked = not actually implemented.
        if not _blank(design_ref) and not _blank(test_ref) and _blank(code_ref):
            issues.append({
                "type": "REQ_NOT_IMPLEMENTED",
                "message": f"{req_id}: has design_ref and test_ref but empty code_ref (designed + tested, not implemented)",
                "req_id": req_id,
                "auto_fixable": False,
            })
    return issues


def validate(tasks_path: str, matrix_path: str | None = None, project_root: str = ".") -> dict:
    issues: list[dict] = []
    tasks_text = Path(tasks_path).read_text(encoding="utf-8")
    issues.extend(check_done_tasks(tasks_text))
    checked = ["DONE tasks have an assigned test (test_refs)"]
    if matrix_path:
        matrix_text = Path(matrix_path).read_text(encoding="utf-8")
        issues.extend(check_matrix(matrix_text, project_root))
        checked += ["matrix code_ref files exist on disk", "REQ designed + tested ⇒ implemented"]

    structure_ok = not issues
    v = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked,
        not_checked=["whether the code actually fulfils the task (LLM review / acceptance)"],
    )
    v.update({"valid": structure_ok, "total_issues": len(issues), "issues": issues})
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Phase 3 implementation reality (D2).")
    ap.add_argument("--tasks", required=True, help="Path to task-breakdown.md")
    ap.add_argument("--matrix", help="Path to traceability matrix")
    ap.add_argument("--project-root", default=".", help="Root for resolving code_ref paths")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    try:
        result = validate(args.tasks, args.matrix, args.project_root)
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"error": f"not readable: {exc}", "valid": False}, ensure_ascii=False))
        return 2

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write output {args.output}: {exc}", "valid": False}, ensure_ascii=False))
            return 2
    else:
        print(text)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
