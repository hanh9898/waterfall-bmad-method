#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Acceptance hard-guards — conditions under which acceptance MUST NOT be ACCEPTED
(B16-1, B16-2). The cardinal Phase-4 sin is a false-ACCEPT: signing off a feature
that "passed" against the WRONG model, or whose coverage is green but incomplete.

Coverage alone is NECESSARY-BUT-NOT-SUFFICIENT for acceptance. This engine does the
deterministic structural part of "may we even consider ACCEPT?": it reconciles the
design model, the matrix, and the upstream spec version against the evidence. A
non-empty block here means **ACCEPT is forbidden** until resolved — the decision
falls to REJECTED/PENDING, never a fabricated green.

Guards (structure-only; the accept JUDGEMENT itself stays with the owner/LLM):
  - B16-1 model-match: D-19 design model tokens vs the code (``model_drift``,
    shared) — accepting a feature whose code never built the designed model is
    accepting the WRONG model. ``accept_blocked`` when drift present.
  - B16-1 matrix completeness: REQ defined in D-02 but no matrix row
    (``missing_from_matrix``, shared) — an untraced REQ is not "done"; accepting is
    accepting an incomplete slice.
  - B16-3 D-27 stale: D-27/D-26 citing a stale D-02 version (``version_coherence``,
    shared) — acceptance evidence built on a superseded spec.
  - B16-2 coverage-not-sufficient: coverage at/above threshold does NOT by itself
    license ACCEPT while any structural guard fires; surfaced so a green coverage
    number can't paper over a blocking guard (advisory note, always emitted).

``accept_allowed`` is True only when every hard guard is clean AND ≥1 guard ran.
A run with nothing to check yields ``accept_allowed: false`` with a note — silence
is not consent to accept.

Exit codes: 0 accept-allowed (structurally), 1 accept-blocked, 2 unreadable
required input / arg error.
"""
from __future__ import annotations

import argparse
import json
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
        doc_version,
        missing_from_matrix,
        model_drift,
        verdict,
        version_coherence,
    )
except ModuleNotFoundError:
    print(json.dumps({
        "error": "Shared lib 'hbc_validation' not found.",
        "suggestion": "Expected at <skills>/hbc-shared/lib/. Install the hbc-shared component alongside this skill.",
    }, ensure_ascii=False))
    sys.exit(2)

DEFAULT_CODE_GLOB = "models/**/*.py"


def _read(path: str | None) -> str | None:
    if not path:
        return None
    try:
        return Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _read_code(code_dir: str | None, glob: str) -> str | None:
    if not code_dir:
        return None
    root = Path(code_dir)
    if not root.exists():
        print(f"WARNING: --code-dir does not exist, model-match skipped: {code_dir}", file=sys.stderr)
        return None
    parts: list[str] = []
    for p in sorted(root.glob(glob)):
        try:
            parts.append(p.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
    return "\n".join(parts)


def guards(
    d02_text: str | None = None,
    d19_text: str | None = None,
    code_text: str | None = None,
    matrix_text: str | None = None,
    d27_text: str | None = None,
    d26_text: str | None = None,
    coverage_pct: float | None = None,
    coverage_threshold: float = 80.0,
) -> dict:
    result: dict = {"checked": [], "blocking": []}
    blocked = False
    checked_any = False

    # --- B16-1 model-match: code built the DESIGNED model (no drift) ---
    if d19_text is not None and code_text is not None:
        result["checked"].append("model-match")
        checked_any = True
        md = model_drift(d19_text, code_text)
        if md["drift"]:
            result["model_drift"] = {"design_only": md["design_only"], "code_only": md["code_only"]}
            result["blocking"].append("model_drift")
            blocked = True

    # --- B16-1 matrix completeness: every D-02 REQ has a matrix row ---
    if d02_text is not None and matrix_text is not None:
        result["checked"].append("matrix-completeness")
        checked_any = True
        missing = missing_from_matrix(d02_text, matrix_text)
        if missing:
            result["missing_from_matrix"] = missing
            result["blocking"].append("missing_from_matrix")
            blocked = True

    # --- B16-3 D-27 stale: acceptance evidence not built on a superseded spec ---
    if d02_text is not None:
        declared = doc_version(d02_text)
        if declared is not None:
            citing: dict[str, str] = {}
            if d27_text is not None:
                citing["D-27"] = d27_text
            if d26_text is not None:
                citing["D-26"] = d26_text
            if citing:
                result["checked"].append("d27-stale")
                checked_any = True
                stale = version_coherence({"D-02": declared}, citing)
                if stale:
                    result["stale_citations"] = stale
                    result["blocking"].append("stale_citations")
                    blocked = True

    # --- B16-2 coverage necessary-but-not-sufficient (advisory, always emitted) ---
    if coverage_pct is not None:
        result["coverage"] = {
            "pct": coverage_pct,
            "threshold": coverage_threshold,
            "meets_threshold": coverage_pct >= coverage_threshold,
        }
    result["coverage_note"] = (
        "Coverage meeting threshold is NECESSARY-BUT-NOT-SUFFICIENT for ACCEPT: a "
        "blocking guard above forbids ACCEPT regardless of coverage; and even with "
        "all guards clean, structural sanity (a fixture actually activates the "
        "branch under test) is an LLM/human judgement, not a number."
    )

    accept_allowed = (not blocked) and checked_any
    v = verdict(
        accept_allowed,
        semantic_review=SEMANTIC_NA,
        checked=[
            "model-match: code built the D-19-designed model, no drift (if D-19 + code)",
            "matrix completeness: every D-02 REQ has a matrix row (if D-02 + matrix)",
            "D-27/D-26 not citing a stale D-02 version (if D-02 + D-27/D-26)",
            "coverage vs threshold reported (necessary-but-not-sufficient)",
        ],
        not_checked=[
            "the ACCEPT/REJECT/DEFER/PENDING JUDGEMENT itself (owner/LLM — domain decision)",
            "whether a fixture structurally activates the branch (anti-false-green sanity, LLM/human)",
            "whether a deferral of a surfaced gap is acceptable (domain decision — ASK)",
            "UX↔mockup acceptance criteria when Part-D active (advisory forward-ref T3.14)",
        ],
    )
    if not checked_any:
        v["note"] = ("No guard input given (need D-19+code, D-02+matrix, or D-02+D-27/D-26); "
                     "nothing reconciled — ACCEPT not licensed by silence.")
    v.update(result)
    v["accept_allowed"] = accept_allowed
    v["accept_blocked"] = blocked
    return v


def main() -> int:
    parser = argparse.ArgumentParser(description="Acceptance hard-guards: conditions that forbid ACCEPT (B16-1/B16-2/B16-3).")
    parser.add_argument("--d02", help="Path to D-02 requirements")
    parser.add_argument("--d19", help="Path to D-19 ER diagram (model-match design side)")
    parser.add_argument("--code-dir", dest="code_dir", help="Feature code root (model-match code side)")
    parser.add_argument("--code-glob", dest="code_glob", default=DEFAULT_CODE_GLOB,
                        help=f"Glob under --code-dir for persistent-model source (default: {DEFAULT_CODE_GLOB})")
    parser.add_argument("--matrix", help="Path to the per-feature traceability matrix")
    parser.add_argument("--d27", help="Path to D-27 test spec (stale-citation check)")
    parser.add_argument("--d26", help="Path to D-26 test plan (stale-citation check)")
    parser.add_argument("--coverage", type=float, help="Observed coverage percent (for the necessary-but-not-sufficient note)")
    parser.add_argument("--threshold", type=float, default=80.0, help="Coverage threshold (default: 80)")
    parser.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    code_text = _read_code(args.code_dir, args.code_glob)
    d19_text = _read(args.d19)
    if (d19_text is None) != (code_text is None):
        print("WARNING: model-match needs BOTH --d19 and --code-dir; only one given → model-match skipped.",
              file=sys.stderr)
        d19_text = None
        code_text = None

    result = guards(
        d02_text=_read(args.d02),
        d19_text=d19_text,
        code_text=code_text,
        matrix_text=_read(args.matrix),
        d27_text=_read(args.d27),
        d26_text=_read(args.d26),
        coverage_pct=args.coverage,
        coverage_threshold=args.threshold,
    )

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        try:
            Path(args.output).write_text(text, encoding="utf-8")
        except OSError as exc:
            print(json.dumps({"error": f"cannot write output {args.output}: {exc}", "accept_allowed": False}, ensure_ascii=False))
            return 2
        print(f"Acceptance-guards report written to {args.output}", file=sys.stderr)
    else:
        print(text)

    return 0 if result["accept_allowed"] else 1


if __name__ == "__main__":
    sys.exit(main())
