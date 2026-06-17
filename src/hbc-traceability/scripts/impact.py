#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Impact (cascade sync) deterministic core for hbc-traceability.

Read-only. The LLM applies judgment on top (apply/verify labels, semantic
review, suggestion wording); this script only computes what is deterministic.

Subcommands:
  detect   git changed-set (working tree vs HEAD, or --since) + user-declared,
           normalized to REQ ids via matrix reverse-lookup (code/test/design_ref).
  analyze  artifact-centric impact over the matrix: apply (vertical spread) +
           verify (horizontal spread), deduped, with a flood guard for shared artifacts.
  freeze   freeze-check per REQ: combine matrix gate_status + task-breakdown
           status + phase-gate reports; priority task > gate > matrix.

Exit codes: 0 ok · 1 error/blocked · 2 no-op (empty changeset).
"""

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from glob import glob as _glob
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Namespace-aware (v2): matches REQ-<FEAT>-NNN / REQ-SHARED-NNN + legacy REQ-NNN.
REQ_ID_RE = re.compile(r"REQ-(?:[A-Z0-9]+-)?\d{3,}")
REF_COLUMNS = ["design_ref", "code_ref", "test_ref"]


def _load_parse_matrix():
    """Reuse parse_matrix from the sibling trace-report.py (hyphenated filename
    → import by path) so matrix parsing stays single-sourced."""
    tr_path = Path(__file__).with_name("trace-report.py")
    spec = importlib.util.spec_from_file_location("trace_report", tr_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_matrix


def _emit(obj: dict, code: int = 0):
    print(json.dumps(obj, indent=2, ensure_ascii=False))
    sys.exit(code)


def _split(cell: str) -> list[str]:
    """Split a matrix ref cell into individual ref tokens."""
    return [t.strip() for t in re.split(r"[,;]", cell or "") if t.strip()]


# --------------------------------------------------------------------------- detect
def _git(root: str, *args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(
            ["git", "-C", root, *args],
            capture_output=True, text=True, encoding="utf-8",
        )
        return p.returncode, (p.stdout or "")
    except FileNotFoundError:
        return 127, ""


def cmd_detect(args):
    parse_matrix = _load_parse_matrix()
    matrix_p = Path(args.matrix)
    if not matrix_p.exists():
        _emit({"blocked": "matrix_not_found", "matrix": args.matrix,
               "suggestion": "Run 'traceability init' first."}, 1)

    rows = parse_matrix(str(matrix_p))
    matrix_reqs = {r["req_id"] for r in rows if r.get("req_id")}

    # declared (primary source)
    declared = [d.strip() for d in re.split(r"[,\s]+", args.declared or "") if d.strip()]
    declared_valid = [d for d in declared if d in matrix_reqs]
    declared_invalid = [d for d in declared if d not in matrix_reqs]  # #1

    # git corroboration
    rc, _ = (0, "") if not args.since else _git(args.project_root, "rev-parse", "--verify", args.since)
    if args.since and rc != 0:
        _emit({"blocked": "invalid_since", "since": args.since}, 1)  # #16
    diff_target = args.since if args.since else "HEAD"
    rc, out = _git(args.project_root, "diff", "--name-only", diff_target)
    git_files = [f.strip() for f in out.splitlines() if f.strip()] if rc == 0 else []
    rc2, out2 = _git(args.project_root, "ls-files", "--others", "--exclude-standard")
    if rc2 == 0:
        git_files += [f.strip() for f in out2.splitlines() if f.strip()]
    git_files = sorted(set(git_files))

    # reverse-map changed files → REQ via code_ref (and test/design substrings)
    git_reqs: set[str] = set()
    untraced: list[str] = []
    for f in git_files:
        base = Path(f).name
        hit = False
        for r in rows:
            joined = " ".join(r.get(c, "") for c in REF_COLUMNS)
            if base and (f in joined or base in joined):
                git_reqs.add(r["req_id"]); hit = True
        # a changed planning doc may carry REQ ids in its path/name
        for m in REQ_ID_RE.findall(f):
            if m in matrix_reqs:
                git_reqs.add(m); hit = True
        if not hit:
            untraced.append(f)  # #4

    changed_set = sorted(set(declared_valid) | git_reqs)
    if not changed_set and not declared_invalid and not untraced:
        _emit({"status": "noop", "message": "Đã đồng bộ — không có thay đổi",
               "changed_set": []}, 2)  # #3

    _emit({
        "status": "ok",
        "changed_set": changed_set,
        "declared": declared_valid,
        "declared_invalid": declared_invalid,
        "git_changed_files": git_files,
        "git_suggested_reqs": sorted(git_reqs),
        "untraced_changes": untraced,
        "baseline": diff_target,
    })


# -------------------------------------------------------------------------- analyze
def cmd_analyze(args):
    parse_matrix = _load_parse_matrix()
    matrix_p = Path(args.matrix)
    if not matrix_p.exists():
        _emit({"blocked": "matrix_not_found", "matrix": args.matrix}, 1)
    rows = parse_matrix(str(matrix_p))
    by_req = {r["req_id"]: r for r in rows if r.get("req_id")}

    changed = [c.strip() for c in re.split(r"[,\s]+", args.changed or "") if c.strip()]
    if not changed:
        _emit({"status": "noop", "changed": []}, 2)

    unknown = [c for c in changed if c not in by_req]  # #5 deleted/unknown
    incomplete = []  # #6 rows with all refs empty

    apply_items: list[dict] = []
    changed_refs: dict[str, str] = {}  # ref -> column
    for req in changed:
        row = by_req.get(req)
        if not row:
            continue
        refs_here = 0
        for col in REF_COLUMNS:
            for ref in _split(row.get(col, "")):
                apply_items.append({"req": req, "column": col, "ref": ref, "kind": "apply"})
                changed_refs[ref] = col
                refs_here += 1
        if refs_here == 0:
            incomplete.append(req)

    # verify: other REQs sharing any changed ref
    verify_items: list[dict] = []
    flood: list[dict] = []
    for ref, col in changed_refs.items():
        sharers = []
        for r in rows:
            rq = r.get("req_id")
            if not rq or rq in changed:
                continue
            for c in REF_COLUMNS:
                cell = r.get(c, "")
                if ref and (ref in cell or any(ref == t for t in _split(cell))):
                    sharers.append(rq)
                    verify_items.append({"req": rq, "shared_ref": ref,
                                         "via_column": c, "kind": "verify"})
                    break
        if len(sharers) > args.flood_threshold:
            flood.append({"ref": ref, "count": len(sharers)})  # #7

    # dedup verify by (req, shared_ref)
    seen = set(); deduped_verify = []
    for v in verify_items:
        k = (v["req"], v["shared_ref"])
        if k not in seen:
            seen.add(k); deduped_verify.append(v)

    _emit({
        "status": "ok",
        "changed": changed,
        "apply": apply_items,
        "verify": deduped_verify,
        "flood": flood,
        "unknown_reqs": unknown,
        "incomplete_rows": incomplete,
    })


# --------------------------------------------------------------------------- freeze
_TASK_ROW_RE = re.compile(
    r"\|\s*(TASK-\d{3,})\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|"
)


def _task_statuses(path: str) -> list[dict]:
    """Parse task-breakdown rows: returns [{task, design_ref, test_refs, status}]."""
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for m in _TASK_ROW_RE.finditer(p.read_text(encoding="utf-8")):
        task, _desc, design, test_refs, _prio, status, _deps = (g.strip() for g in m.groups())
        out.append({"task": task, "design_ref": design,
                    "test_refs": test_refs, "status": status.upper()})
    return out


def _gate_status(glob_pat: str, root: str) -> str | None:
    """Coarsest phase-gate signal: PASSED only if every found gate report says PASSED.

    glob_pat is expected resolved (caller substitutes {output_folder}); absolute
    patterns are used as-is, relative ones resolve against root. Uses glob.glob so
    an absolute pattern never trips Path.glob's relative-only restriction.
    """
    pat = glob_pat if Path(glob_pat).is_absolute() else str(Path(root) / glob_pat)
    files = [Path(p) for p in _glob(pat)]
    if not files:
        return None
    seen_pass = False
    for f in files:
        txt = f.read_text(encoding="utf-8", errors="ignore").upper()
        if "FAIL" in txt:
            return "FAILED"
        if "PASS" in txt:
            seen_pass = True
    return "PASSED" if seen_pass else None


def cmd_freeze(args):
    parse_matrix = _load_parse_matrix()
    matrix_p = Path(args.matrix)
    if not matrix_p.exists():
        _emit({"blocked": "matrix_not_found", "matrix": args.matrix}, 1)
    rows = parse_matrix(str(matrix_p))
    by_req = {r["req_id"]: r for r in rows if r.get("req_id")}

    tasks = _task_statuses(args.task_breakdown) if args.task_breakdown else []
    has_tasks = bool(tasks)
    phase_gate = _gate_status(args.gate_reports_glob, args.project_root) if args.gate_reports_glob else None

    reqs = [c.strip() for c in re.split(r"[,\s]+", args.reqs or "") if c.strip()]
    results = []
    for req in reqs:
        row = by_req.get(req, {})
        matrix_gate = (row.get("gate_status") or "").upper()
        # task signal: a task whose design_ref/test_refs mentions this req's refs
        task_status = None
        refs_text = " ".join(row.get(c, "") for c in REF_COLUMNS)
        for t in tasks:
            blob = f"{t['design_ref']} {t['test_refs']}"
            if req in blob or (refs_text and any(
                    tok and tok in blob for tok in _split(refs_text))):
                # most-advanced status wins among matches (DONE > IN_PROGRESS > TODO)
                order = {"DONE": 3, "IN_PROGRESS": 2, "TODO": 1}
                if order.get(t["status"], 0) > order.get(task_status or "", 0):
                    task_status = t["status"]
        # priority: task > phase-gate > matrix
        if task_status:
            frozen = task_status == "DONE"
            source = "task"
        elif phase_gate:
            frozen = phase_gate == "PASSED"
            source = "phase-gate"
        elif matrix_gate:
            frozen = matrix_gate == "PASSED"
            source = "matrix"
        else:
            frozen = False
            source = "none"  # fallback: treat as updatable, surface for LLM
        results.append({
            "req": req, "frozen": frozen, "decided_by": source,
            "task_status": task_status, "phase_gate": phase_gate,
            "matrix_gate_status": matrix_gate or None,
        })

    _emit({
        "status": "ok",
        "has_task_breakdown": has_tasks,
        "phase_gate": phase_gate,
        "results": results,
    })


# -------------------------------------------------------------------------- complete
def cmd_complete(args):
    """Cascade completeness: which changed-set nodes lack a terminal disposition.

    Reads the cascade state file (prompt-managed) whose `dispositions` map records
    each node's terminal outcome (reconciled / deferred / frozen_task / blocked).
    Deterministic set-difference so the prompt never re-walks the state by hand.
    """
    changed = [c.strip() for c in re.split(r"[,\s]+", args.changed or "") if c.strip()]
    if not changed:
        _emit({"status": "ok", "accounted": [], "missing": []})
    dispositions: dict = {}
    state_p = Path(args.state)
    if state_p.exists():
        try:
            dispositions = (json.loads(state_p.read_text(encoding="utf-8")) or {}).get("dispositions", {}) or {}
        except (ValueError, OSError):
            _emit({"blocked": "state_unreadable", "state": args.state}, 1)
    accounted = [c for c in changed if c in dispositions]
    missing = [c for c in changed if c not in dispositions]
    _emit({
        "status": "ok",
        "complete": not missing,
        "accounted": accounted,
        "missing": missing,
        "dispositions": {k: dispositions[k] for k in accounted},
    })


def main():
    ap = argparse.ArgumentParser(description="Impact (cascade sync) deterministic core.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("detect", help="git + declared → changed REQ set")
    d.add_argument("--matrix", required=True)
    d.add_argument("--declared", default="", help="comma/space-separated REQ ids user declared")
    d.add_argument("--since", default="", help="git ref baseline (default: working tree vs HEAD)")
    d.add_argument("--project-root", default=".")
    d.set_defaults(func=cmd_detect)

    a = sub.add_parser("analyze", help="artifact-centric impact: apply + verify")
    a.add_argument("--matrix", required=True)
    a.add_argument("--changed", required=True, help="comma/space-separated changed REQ ids")
    a.add_argument("--flood-threshold", type=int, default=20)
    a.add_argument("--project-root", default=".")
    a.set_defaults(func=cmd_analyze)

    f = sub.add_parser("freeze", help="freeze-check per REQ (task > gate > matrix)")
    f.add_argument("--matrix", required=True)
    f.add_argument("--reqs", required=True, help="comma/space-separated REQ ids")
    f.add_argument("--task-breakdown", default="")
    f.add_argument("--gate-reports-glob", default="")
    f.add_argument("--project-root", default=".")
    f.set_defaults(func=cmd_freeze)

    c = sub.add_parser("complete", help="cascade completeness: changed-set minus accounted dispositions")
    c.add_argument("--state", required=True, help="path to cascade state json (.cascade-state.json)")
    c.add_argument("--changed", required=True, help="comma/space-separated changed REQ ids")
    c.set_defaults(func=cmd_complete)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
