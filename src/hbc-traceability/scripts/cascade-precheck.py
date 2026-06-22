#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Cascade pre-check gate for hbc-traceability (B7-1/B7-3/B7-5/B7-6).

The deterministic gate the complete/phase-transition step honors before a
document with downstream consumers is allowed to close. It does NOT edit
anything (impact stays READ-only); it reads the sources of truth and emits a
single blocking verdict so the cascade is ENFORCED rather than advisory.

What it checks (all structure-only, judgment stays with the LLM/readiness layer):

  B7-6  cascade pre-check — D-02 defines REQs the matrix never received a row for,
        or matrix rows have a blank trace column. Either → BLOCK `untraced_change`
        and prompt backfill. Reuses shared `missing_from_matrix` +
        `matrix_coverage_gaps` (the "39/39 green but 040/041/042 never added"
        RCA failure).
  B7-1  cascade ENFORCED — when downstream-affected docs exist (the matrix carries
        rows past the upstream that changed) and the matrix is NOT clean, the
        verdict is `blocked` with `cascade_required=true`: the workflow may not
        reach "complete"/phase-transition until impact has run + backfilled.
  B7-3  drift-watch (minimal) — an upstream doc whose declared version moved AHEAD
        of the version the matrix/task-breakdown/gate cite (stale citation). Reuses
        shared `doc_version` + `version_coherence`. NOT the build-graph kernel.
  B7-5  structural-change route — a core/shared model declared in the design (D-19)
        but absent from the per-feature code, i.e. a model change that likely
        crosses features → ROUTE to a "consider rebaseline" warning (the actual
        cross-feature engine is hbc-rebaseline / TA.7, NOT built here).

B7-4 (reconcile-adversarial) is a PROSE discipline in references/impact-capability.md,
not a script knob — this gate's deterministic evidence (the sets below) IS the
independent lens the skeptic reconciles against; it never self-grades.

Honest verdict via shared `verdict`: structure-only, semantic adequacy is N/A here.
A CLEAN matrix on a broken fixture is the cardinal sin — every set defaults to
"surface the gap", never to a silent pass.

Run with `python` (Windows dev) or `python3` (Linux/Mac CI):
    python3 {skill-root}/scripts/cascade-precheck.py --d02 D-02.md --matrix matrix.md \\
        [--d27 D-27.md] [--task-breakdown tb.md] [--gate-reports-glob '.../phase-*-gate.md'] \\
        [--design D-19.md --code-dir code/] [--strict | --assumptions-allowed]

Exit: 0 clean (no block) · 1 blocked (untraced_change / cascade_required) · 2 io error.
"""
from __future__ import annotations

import argparse
import glob as _glob
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- shared lib bootstrap (parents[2] → hbc-shared/lib) ---
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_validation import (  # noqa: E402
        SEMANTIC_NA,
        REQ_ID_RE,
        doc_version,
        matrix_coverage_gaps,
        missing_from_matrix,
        model_drift,
        parse_matrix,
        req_num_map,
        verdict,
        version_coherence,
    )
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install hbc-shared alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)


def _read(path: str | None) -> str | None:
    if not path:
        return None
    return Path(path).read_text(encoding="utf-8")


def _read_glob(pattern: str | None) -> dict[str, str]:
    """label→text for every file matching a (possibly absolute) glob. Returns {} if
    no pattern / no matches — drift-watch then simply has nothing to cite-check."""
    if not pattern:
        return {}
    out: dict[str, str] = {}
    for p in sorted(_glob.glob(pattern, recursive=True)):
        try:
            out[Path(p).name] = Path(p).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
    return out


def _read_code_dir(code_dir: str | None) -> str:
    """Concatenate persistent-model code (models/**/*.py) for the drift route (B7-5).
    Mirrors hbc-check-implementation-readiness: only persistent models, not wizards."""
    if not code_dir:
        return ""
    root = Path(code_dir)
    if not root.exists():
        return ""
    parts: list[str] = []
    for p in sorted(root.glob("models/**/*.py")):
        try:
            parts.append(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    return "\n".join(parts)


def precheck(
    d02_text: str,
    matrix_text: str,
    *,
    d27_text: str | None = None,
    citing_texts: dict[str, str] | None = None,
    design_text: str | None = None,
    code_text: str | None = None,
) -> dict:
    """Run the cascade pre-check; return the blocking verdict + evidence sets."""
    blockers: list[dict] = []
    warnings: list[dict] = []

    # --- B7-6: matrix missing required rows + blank trace columns (untraced change) ---
    _, slugs = req_num_map(d02_text)
    multi_feature = len(slugs) > 1

    missing_rows = missing_from_matrix(d02_text, matrix_text)
    coverage_gaps = matrix_coverage_gaps(matrix_text)

    # Silent-green guard: matrix mentions REQ ids but no parseable table → cannot
    # assert coverage; that is the loudest false-green, surface it as a block.
    _, mrows = parse_matrix(matrix_text)
    no_table = (not mrows) and bool(REQ_ID_RE.search(matrix_text or ""))
    if no_table:
        blockers.append({
            "type": "NO_MATRIX_TABLE",
            "message": "matrix mentions REQ ids but no parseable table was found",
        })

    if missing_rows:
        blockers.append({
            "type": "MISSING_FROM_MATRIX",
            "message": f"{len(missing_rows)} REQ defined in D-02 have no matrix row: "
                       f"{', '.join(missing_rows)}",
            "req_ids": missing_rows,
        })
    if coverage_gaps:
        blockers.append({
            "type": "UNTRACED_COLUMN",
            "message": f"{len(coverage_gaps)} matrix row(s) have a blank trace column",
            "gaps": coverage_gaps,
        })

    # --- B7-3: drift-watch — upstream doc version moved ahead of its citations ---
    drift_watch: list[dict] = []
    d02_ver = doc_version(d02_text)
    if d02_ver and citing_texts:
        # The matrix itself carries no frontmatter version; cite-check the downstream
        # consumers (task-breakdown, gate reports, D-27) that pin a D-02 version.
        authority = {"D-02": d02_ver}
        for issue in version_coherence(authority, citing_texts):
            drift_watch.append(issue)
    if drift_watch:
        warnings.append({
            "type": "VERSION_DRIFT",
            "message": f"{len(drift_watch)} citation(s) pin a stale upstream version "
                       f"(D-02 is v{d02_ver})",
            "citations": drift_watch,
        })

    # --- B7-5: structural-change → rebaseline ROUTE (light touchpoint only) ---
    structural_route: list[str] = []
    if design_text is not None and code_text is not None:
        drift = model_drift(design_text, code_text)
        structural_route = drift.get("design_only", [])
        if structural_route:
            warnings.append({
                "type": "STRUCTURAL_CHANGE",
                "message": f"{len(structural_route)} design model(s) absent from code "
                           f"(possible core/shared change crossing features) — consider "
                           f"`hbc-rebaseline` (cross-feature engine, TA.7); this is a routing "
                           f"note only, not the rebaseline itself",
                "models": structural_route,
            })

    # --- B7-1: cascade ENFORCED verdict ---
    # downstream_present = the matrix HAS rows (there is a downstream to keep in sync).
    downstream_present = bool(mrows)
    structure_ok = not blockers
    # cascade_required: there is a downstream AND it is not clean → the workflow is
    # BLOCKED from complete/phase-transition until impact runs + backfills.
    cascade_required = downstream_present and not structure_ok

    v = verdict(
        structure_ok,
        semantic_review=SEMANTIC_NA,
        checked=[
            "every D-02 REQ has a matrix row (B7-6)",
            "every matrix row traces design/code/test (B7-6)",
            "downstream citations are not stale vs D-02 version (B7-3)",
        ],
        not_checked=[
            "whether each trace is semantically correct (LLM / readiness)",
            "cross-feature rebaseline itself (routed to hbc-rebaseline / TA.7)",
        ],
    )
    # The blocking reason the complete/gate step honors (closed set, matches the
    # impact headless contract): untraced_change for a missing/blank matrix, else clean.
    reason = "untraced_change" if blockers else None
    v.update({
        "valid": structure_ok,
        "blocked": bool(blockers),
        "reason": reason,
        "cascade_required": cascade_required,
        "downstream_present": downstream_present,
        "blockers": blockers,
        "warnings": warnings,
        "missing_from_matrix": missing_rows,
        "coverage_gaps": coverage_gaps,
        "drift_watch": drift_watch,
        "structural_route": structural_route,
    })
    if multi_feature:
        v["multi_feature_warning"] = (
            f"multiple feature slugs detected ({sorted(slugs)}); trailing-number "
            "identity may collide — counts unreliable"
        )
    return v


def main() -> int:
    ap = argparse.ArgumentParser(description="Cascade pre-check gate (B7-1/B7-3/B7-5/B7-6).")
    ap.add_argument("--d02", required=True, help="Path to D-02 requirements (source of truth)")
    ap.add_argument("--matrix", required=True, help="Path to the per-feature traceability matrix")
    ap.add_argument("--d27", help="Path to D-27 (cite-checked for stale D-02 version)")
    ap.add_argument("--task-breakdown", help="Path to task-breakdown (cite-checked for stale version)")
    ap.add_argument("--gate-reports-glob", help="Glob of phase-gate reports (cite-checked)")
    ap.add_argument("--design", help="Path to D-19 design (structural-change route, needs --code-dir)")
    ap.add_argument("--code-dir", help="Feature code root (models/**/*.py) for the structural route")
    # A5 autonomy: CI default infers + logs + continues (non-green), never blocks the
    # first turn; --strict stops at the first surfaced gap for a human.
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--strict", action="store_true",
                      help="exit 1 on ANY surfaced gap (stop for a human)")
    mode.add_argument("--assumptions-allowed", action="store_true",
                      help="CI default: report gaps as real (non-green), still exit 1 when blocked")
    ap.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    try:
        d02 = _read(args.d02)
        matrix = _read(args.matrix)
        d27 = _read(args.d27)
        design = _read(args.design)
        code = _read_code_dir(args.code_dir) if args.code_dir else None
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"error": f"not readable: {exc}", "valid": False}, ensure_ascii=False))
        return 2

    # Cite-check sources for drift-watch (B7-3): downstream docs that pin a D-02 version.
    citing: dict[str, str] = {}
    try:
        if args.task_breakdown:
            citing["task-breakdown"] = _read(args.task_breakdown) or ""
        if d27 is not None:
            citing["D-27"] = d27
        citing.update(_read_glob(args.gate_reports_glob))
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"error": f"citing source not readable: {exc}", "valid": False}, ensure_ascii=False))
        return 2

    result = precheck(
        d02, matrix,
        d27_text=d27,
        citing_texts=citing or None,
        design_text=design,
        code_text=code,
    )

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write {args.output}: {exc}", "valid": False}, ensure_ascii=False))
            return 2
    else:
        print(text)

    # A block always exits 1. --strict additionally exits 1 when only warnings exist
    # (stop for a human to confirm a deferral). Default / --assumptions-allowed:
    # warnings alone are non-blocking (CI continues, having logged them), but a real
    # block still exits 1 — CI never gets a false green from an unconfirmed gap.
    if result["blocked"]:
        return 1
    if args.strict and result["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
