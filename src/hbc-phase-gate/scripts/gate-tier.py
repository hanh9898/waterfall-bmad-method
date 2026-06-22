#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""TA.4 — tier-aware gate verdict (must-knockout / should-scorecard).

WHAT THIS IS
============
The U16 evaluator (`evaluate-gate-checklist.py`) scores every checklist item and
folds them into ONE `overall_status`. That is correct but flat: a thin-but-not-
broken recommendation (a missing nice-to-have) and a factually-wrong correctness
item both land in the same `FAILED` bucket, so the report cannot say *"the gate is
blocked on a real defect"* vs *"the gate is clean on must-haves, scoring 7/9 on
should-haves"*. TA.4 splits the checklist into two TIERS and emits a tier-aware
verdict on top of the evaluator's per-item results — WITHOUT touching the
evaluator (this module consumes its JSON):

  * MUST (knockout) — correctness + required items. ANY must-FAIL (or unresolved
    CONTESTED / BLOCKED on a must item) is a KNOCKOUT → the gate FAILS, full stop.
    This is exactly the existing knockout behaviour (`required_failed` /
    `correctness_failed` block); TA.4 only makes the tier EXPLICIT in the verdict.
  * SHOULD (scorecard) — quality/recommended items that are NOT required and NOT
    correctness. These are SCORED (N/M passed) and reported as a scorecard. A low
    scorecard does NOT hard-block; per policy it may WARN/CONTEST, but a should-fail
    can never knock the gate out and can never silently pass a must.

TIER ASSIGNMENT (load-bearing — mirrors `_is_correctness_item` exactly)
=======================================================================
A result is MUST when it is a correctness item (entry-gate / `[MATRIX]` /
`[correctness]`-tagged) OR it is `required`. Everything else is SHOULD. This is
the prompt's rule: the existing correctness/required items are MUST; others default
SHOULD. Because correctness ⊆ required in the evaluator's own classification, MUST
is effectively *required ∪ correctness* and the knockout set never shrinks relative
to U16 — a SHOULD-fail can NEVER demote a MUST.

TIER-AWARE VERDICT
==================
Returns `{tier_verdict, knockout, scorecard, ...}`:
  * `knockout` — `FAILED` if any must item FAILs / is CONTESTED-required /
    BLOCKED-required; else `PASSED`. (A must CONTESTED is a knockout: "can't
    compute a correctness item" is never a pass — parity with U16.)
  * `scorecard` — `{passed, total, ratio}` over SHOULD items that were actually
    evaluated (PENDING_LLM/NA excluded from the denominator — an un-judged or
    waived should is not "failed").
  * `tier_verdict` — the composed verdict honoring U16 precedence:
      BLOCKED (must blocked)  >  FAILED (must knockout)  >
      CONTESTED (must contested)  >  WARNING (should scorecard below floor, lenient
      only)  >  PASSED.
    A must-knockout ALWAYS dominates a perfect scorecard; a poor scorecard NEVER
    dominates a clean knockout (it can only warn).

This module is PURE over the evaluator JSON (deterministic, unit-testable, no I/O
beyond reading the JSON file). It is consumed by `gate-outcome.py` (which feeds the
knockout verdict as its stage-1 status) and surfaced in the gate report. Run with
`python`.
"""
from __future__ import annotations

import argparse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

# Default scorecard floor (fraction of evaluated SHOULD items that must pass before
# a clean-knockout gate is WARNED in lenient mode). Advisory only — never blocks.
DEFAULT_SHOULD_FLOOR = 0.8


def _is_must(result: dict) -> bool:
    """True when a per-item RESULT belongs to the MUST (knockout) tier.

    Mirrors `evaluate-gate-checklist.py::_is_correctness_item` on the data the
    evaluator emits per result (`type`, `required`, `criteria`, `description`,
    `artifact_pattern`) PLUS the rule that any `required` item is MUST. Correctness
    items are MUST even on the off chance they were authored `required=no` (a
    correctness check must never be relegated to the soft tier).
    """
    if result.get("required"):
        return True
    # entry-gate: a required CONTENT check over a prior phase gate report.
    pat = (result.get("artifact_pattern") or "").replace("\\", "/")
    if result.get("type") == "CONTENT" and result.get("required") and "gates/phase-" in pat:
        return True
    if result.get("type") == "MATRIX" and result.get("required"):
        return True
    tagged = "[correctness]" in (result.get("criteria") or "").lower() \
        or "[correctness]" in (result.get("description") or "").lower()
    return bool(result.get("required") and tagged)


def _is_must_fail(result: dict) -> bool:
    """A must item that definitively FAILed (knockout)."""
    return _is_must(result) and result.get("status") == "FAIL"


def tier_verdict(
    results: list[dict],
    gate_mode: str = "strict",
    should_floor: float = DEFAULT_SHOULD_FLOOR,
) -> dict:
    """Compute the tier-aware verdict from the evaluator's per-item results.

    Pure function of its inputs — deterministic, no I/O. See module docstring for
    the tiering rule and verdict precedence.
    """
    must = [r for r in results if _is_must(r)]
    should = [r for r in results if not _is_must(r)]

    must_failed = [r["item_id"] for r in must if r.get("status") == "FAIL"]
    must_contested = [r["item_id"] for r in must if r.get("status") == "CONTESTED"]
    must_blocked = [r["item_id"] for r in must if r.get("status") == "BLOCKED"]

    # Scorecard: only count SHOULD items that were actually evaluated to a binary
    # PASS/FAIL — PENDING_LLM (un-judged), NA (waived), SKIP and CONTESTED are not
    # "failures" of a should and must not drag the denominator.
    scored = [r for r in should if r.get("status") in ("PASS", "FAIL")]
    should_passed = sum(1 for r in scored if r.get("status") == "PASS")
    should_total = len(scored)
    ratio = (should_passed / should_total) if should_total else 1.0

    knockout = "FAILED" if must_failed else "PASSED"

    # Compose the tier verdict with U16 precedence. A must blocked/contested never
    # passes; a should scorecard can only warn, never knock out.
    if must_blocked:
        verdict = "BLOCKED"
        reason = "must_item_blocked"
    elif must_failed:
        verdict = "FAILED"
        reason = "must_knockout"
    elif must_contested:
        verdict = "CONTESTED"
        reason = "must_contested"
    elif gate_mode != "strict" and should_total and ratio < should_floor:
        # Clean on must-haves but the soft scorecard is below floor: in lenient mode
        # surface a WARNING (accepted risk), never a block. Strict mode does not warn
        # on shoulds — a clean knockout is simply PASSED.
        verdict = "WARNING"
        reason = "should_scorecard_below_floor"
    else:
        verdict = "PASSED"
        reason = "must_clean"

    return {
        "tier_verdict": verdict,
        "reason": reason,
        "knockout": {
            "status": knockout,
            "must_total": len(must),
            "must_failed": must_failed,
            "must_contested": must_contested,
            "must_blocked": must_blocked,
        },
        "scorecard": {
            "passed": should_passed,
            "total": should_total,
            "ratio": round(ratio, 4),
            "floor": should_floor,
            "below_floor": bool(should_total and ratio < should_floor),
            "not_scored": [
                r["item_id"] for r in should if r.get("status") not in ("PASS", "FAIL")
            ],
        },
        "gate_mode": gate_mode,
    }


def run(eval_json_path: str, gate_mode: str | None = None,
        should_floor: float = DEFAULT_SHOULD_FLOOR) -> dict:
    """Load an evaluate-gate-checklist.py JSON file and compute the tier verdict.

    A BLOCKED evaluator output (crash) is propagated as a BLOCKED tier verdict — a
    crash is never a pass (parity with the evaluator + gate-outcome)."""
    data = json.loads(Path(eval_json_path).read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    # Evaluator crash sentinel: it emits {"status":"BLOCKED",...} with no results.
    if summary.get("overall_status") == "BLOCKED" or data.get("status") == "BLOCKED":
        return {
            "tier_verdict": "BLOCKED",
            "reason": "evaluator_blocked",
            "knockout": {"status": "BLOCKED", "must_total": 0, "must_failed": [],
                         "must_contested": [], "must_blocked": []},
            "scorecard": {"passed": 0, "total": 0, "ratio": 0.0,
                          "floor": should_floor, "below_floor": False, "not_scored": []},
            "gate_mode": gate_mode or summary.get("gate_mode", "strict"),
        }
    mode = gate_mode or summary.get("gate_mode", "strict")
    return tier_verdict(data.get("results", []), mode, should_floor)


def main():
    p = argparse.ArgumentParser(
        description="TA.4 tier-aware gate verdict (must-knockout / should-scorecard).")
    p.add_argument("eval_json", help="JSON file produced by evaluate-gate-checklist.py.")
    p.add_argument("--gate-mode", default=None,
                   help="Override gate_mode (else taken from the eval JSON summary).")
    p.add_argument("--should-floor", type=float, default=DEFAULT_SHOULD_FLOOR,
                   help=f"Scorecard warn floor (lenient only; default {DEFAULT_SHOULD_FLOOR}).")
    p.add_argument("-o", "--output", help="Output file (default stdout).")
    args = p.parse_args()

    result = run(args.eval_json, args.gate_mode, args.should_floor)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Tier verdict written to {args.output}", file=sys.stderr)
    else:
        print(text)
    # Non-zero on anything but a clean PASS — a knockout/contested/blocked gate must
    # never read as exit 0 (parity with the evaluator + gate-outcome).
    sys.exit(0 if result.get("tier_verdict") == "PASSED" else 1)


if __name__ == "__main__":
    # Crash → BLOCKED, never a silent pass (parity with evaluate-gate-checklist.py).
    try:
        main()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 — last-resort: must not become a pass
        import traceback
        print(json.dumps({
            "tier_verdict": "BLOCKED",
            "reason": "tier_evaluator_crashed",
            "evidence": f"{type(exc).__name__}: {exc}",
        }, ensure_ascii=False))
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)
