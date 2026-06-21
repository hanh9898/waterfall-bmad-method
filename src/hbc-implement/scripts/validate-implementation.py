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

# Windows stdout defaults to cp1252 and cannot encode non-ASCII (e.g. Vietnamese)
# JSON emitted with ensure_ascii=False. Force UTF-8 for identical output on Win/macOS.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

# --- shared lib bootstrap (C-1) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        model_drift,
        spec_ref_leaks,
        verdict,
    )
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


_REQ_RE = re.compile(r"REQ-(?:[A-Z0-9]+(?:-[A-Z0-9]+)*-)?\d{3,}")


def check_red_evidence(tasks_text: str, evidence_dir: str) -> list[dict]:
    """TDD soft (cluster 1=C / 3): every DONE task must have RED-evidence — a file
    <evidence_dir>/<TASK>.md recording the FAIL test run before code is written.
    Note: the evidence is self-attested by the agent, NOT a cryptographic proof."""
    issues: list[dict] = []
    d = Path(evidence_dir)
    for m in _TASK_ROW_RE.finditer(tasks_text):
        task_id, _desc, _design, _test, _prio, status, _deps = (g.strip() for g in m.groups())
        if status.lower() != "done":
            continue
        f = d / f"{task_id}.md"
        if not f.exists():
            issues.append({
                "type": "NO_RED_EVIDENCE",
                "message": f"{task_id} is DONE but has no RED-evidence ({f})",
                "task_id": task_id,
                "auto_fixable": False,
            })
            continue
        try:
            body = f.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            body = ""
        if "fail" not in body:
            issues.append({
                "type": "RED_EVIDENCE_NO_FAIL",
                "message": f"{task_id}: RED-evidence shows no sign of a failing test (RED)",
                "task_id": task_id,
                "auto_fixable": False,
            })
    return issues


def _matrix_table(matrix_text: str) -> tuple[dict, list[list[str]]]:
    """Parse matrix → (header_map name→index, data rows). Header-name based, so it
    tolerates both the 7-column matrix (legacy) and the 8-column one (with the new `feature` column)."""
    header: dict = {}
    rows: list[list[str]] = []
    for line in matrix_text.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        joined = "".join(cells)
        if joined and set(joined) <= {"-", " ", ":"}:
            continue  # separator
        low = [c.lower() for c in cells]
        if not header:
            if "req_id" in low:
                header = {name: i for i, name in enumerate(low)}
            continue
        idx = header.get("req_id", 0)
        if idx < len(cells) and _REQ_RE.match(cells[idx]):
            rows.append(cells)
    return header, rows


def _col(cells: list[str], header: dict, name: str) -> str:
    i = header.get(name, -1)
    return cells[i].strip() if 0 <= i < len(cells) else ""


def check_matrix(matrix_text: str, project_root: str) -> list[dict]:
    issues: list[dict] = []
    header, rows = _matrix_table(matrix_text)
    if not header:
        return issues
    for cells in rows:
        req_id = _col(cells, header, "req_id")
        design_ref = _col(cells, header, "design_ref")
        code_ref = _col(cells, header, "code_ref")
        test_ref = _col(cells, header, "test_ref")

        # code_ref tokens that look like file paths must exist on disk.
        if not _blank(code_ref):
            for tok in re.split(r"[,\s]+", code_ref):
                tok = tok.strip().strip("`")
                if not tok or _blank(tok):
                    continue
                # Normalize a Windows separator and strip a trailing :line(:col)
                # reference, so `src\login.py:42` resolves to src/login.py (the
                # raw token is still reported in the message for fidelity).
                norm = tok.replace("\\", "/")
                norm = re.sub(r":\d+(?::\d+)?$", "", norm)
                if "/" in norm or re.search(r"\.\w+$", norm):  # looks like a path
                    p = Path(norm) if Path(norm).is_absolute() else Path(project_root) / norm
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


_CODE_GLOB = "*.py"
# Transient/derived code that is not a persistent data model — excluded from the
# MODEL_DRIFT reconciliation so a wizard/test/controller never reads as a rogue model.
_NON_MODEL_PARTS = {"wizard", "wizards", "test", "tests", "controllers", "migrations"}


def _iter_code_files(code_dir: str, exclude_parts: set[str] | None = None):
    exclude = exclude_parts or set()
    for p in sorted(Path(code_dir).rglob(_CODE_GLOB)):
        if exclude and ({part.lower() for part in p.parts} & exclude):
            continue
        yield p


def check_spec_ref_leak(code_dir: str) -> list[dict]:
    """T1.2 — no REQ-/TC-/NFR- id embedded in source/test. A spec id in code couples
    the implementation to the spec document; when the spec is renumbered, code rots.
    Scans ALL code (prod + test) — the leak target is the whole feature slice."""
    issues: list[dict] = []
    base = Path(code_dir)
    for p in _iter_code_files(code_dir):
        leaks = spec_ref_leaks(p.read_text(encoding="utf-8", errors="replace"))
        if not leaks:
            continue
        rel = str(p.relative_to(base)).replace("\\", "/")
        sample = ", ".join(sorted(set(leaks))[:5])
        issues.append({
            "type": "SPEC_REF_LEAK",
            "message": f"{rel}: {len(leaks)} spec-ref id(s) embedded in source ({sample})",
            "path": rel,
            "count": len(leaks),
            "auto_fixable": False,
        })
    return issues


def check_model_drift(design_path: str, code_dir: str) -> list[dict]:
    """T1.1 — a model declared in D-19 must exist in code and vice-versa (MODEL_DRIFT).

    Persistent-model scope only (wizard/test/controller code excluded) so the
    code↔design reconciliation compares like with like. Catches the RCA case where
    the design moved to a Request+Snapshot model the code never implemented."""
    design = Path(design_path).read_text(encoding="utf-8", errors="replace")
    code_text = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in _iter_code_files(code_dir, _NON_MODEL_PARTS)
    )
    drift = model_drift(design, code_text)
    issues: list[dict] = []
    for tok in drift["design_only"]:
        issues.append({
            "type": "MODEL_DRIFT",
            "message": f"model '{tok}' is in the D-19 design but absent from code (design drift)",
            "token": tok, "direction": "design_only", "auto_fixable": False,
        })
    for tok in drift["code_only"]:
        issues.append({
            "type": "MODEL_DRIFT",
            "message": f"code model '{tok}' is not described in the D-19 design (rogue model)",
            "token": tok, "direction": "code_only", "auto_fixable": False,
        })
    return issues


def validate(tasks_path: str, matrix_path: str | None = None, project_root: str = ".",
             tdd_evidence_dir: str | None = None, code_dir: str | None = None,
             design_path: str | None = None) -> dict:
    issues: list[dict] = []
    tasks_text = Path(tasks_path).read_text(encoding="utf-8")
    # Guard: a --tasks file with no parseable task row would otherwise validate as
    # "complete" with nothing examined (every per-row check is a no-op). Surface it
    # loudly, mirroring validate-task-breakdown's NO_TASKS.
    if not _TASK_ROW_RE.search(tasks_text):
        issues.append({
            "type": "UNPARSEABLE_TASKS",
            "message": "No task rows parsed from --tasks (empty or malformed table). "
                       "Expected: | task_id | description | design_ref | test_refs | priority | status | dependencies |",
            "auto_fixable": False,
        })
    issues.extend(check_done_tasks(tasks_text))
    checked = ["DONE tasks have an assigned test (test_refs)"]
    if tdd_evidence_dir:
        issues.extend(check_red_evidence(tasks_text, tdd_evidence_dir))
        checked += ["DONE tasks have RED-evidence (self-attested failing test)"]
    if matrix_path:
        matrix_text = Path(matrix_path).read_text(encoding="utf-8")
        issues.extend(check_matrix(matrix_text, project_root))
        checked += ["matrix code_ref files exist on disk", "REQ designed + tested ⇒ implemented"]
    if code_dir:
        issues.extend(check_spec_ref_leak(code_dir))
        checked += ["no spec-ref id (REQ-/TC-/NFR-) embedded in code/test (T1.2)"]
        if design_path:
            issues.extend(check_model_drift(design_path, code_dir))
            checked += ["D-19 models ↔ code reconciled, no MODEL_DRIFT (T1.1)"]

    structure_ok = not issues
    v = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=checked,
        not_checked=[
            "whether the code actually fulfils the task (LLM review / acceptance)",
            "RED-evidence is self-attested — no git/timestamp proof against tampering (cluster 1=C)",
        ],
    )
    v.update({"valid": structure_ok, "total_issues": len(issues), "issues": issues})
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate Phase 3 implementation reality (D2).")
    ap.add_argument("--tasks", required=True, help="Path to task-breakdown.md")
    ap.add_argument("--matrix", help="Path to traceability matrix")
    ap.add_argument("--tdd-evidence-dir", help="Dir of RED-evidence files (<TASK>.md) — Phase 3 TDD check")
    ap.add_argument("--project-root", default=".", help="Root for resolving code_ref paths")
    ap.add_argument("--code-dir", help="Code dir to scan for spec-ref leaks (T1.2)")
    ap.add_argument("--design", help="D-19 path for MODEL_DRIFT reconciliation (T1.1; needs --code-dir)")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    try:
        result = validate(args.tasks, args.matrix, args.project_root, args.tdd_evidence_dir,
                          args.code_dir, args.design)
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
