#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""TA.3 — gate two-stage verify + RECYCLE outcome state-machine.

WHAT THIS IS
============
The U16 evaluator (`evaluate-gate-checklist.py`) is **stage 1**: it scores the
phase's checklist items deterministically and yields a verdict
(PASSED/FAILED/CONTESTED/BLOCKED/...). That verdict answers *"are this phase's
own artifacts internally OK?"* — but it cannot see WHY a downstream phase fails:
the real cause is often an **upstream** artifact that drifted after this phase
was built (the stale-D-19, missing-matrix-row class from the RCA).

This module is **stage 2 + the outcome state-machine**. Stage 2 runs the TA.1
build-graph over the feature and asks the orthogonal question *"is any artifact
this phase depends on stale/dirty?"* (`dirty_set`). The two stages then compose:

    PASS    — stage-1 PASSED  AND  no dirty upstream below this phase.
    FAIL    — stage-1 FAILED/CONTESTED  AND  the failure is local
              (no earlier-phase artifact is dirty — fixing it here is enough).
    RECYCLE — an EARLIER phase's artifact is dirty/stale per the build-graph.
              Returning a flat FAIL would send the user to patch THIS phase, but
              the fix belongs upstream. So the gate hands control back to
              phase (n−k) — the phase that OWNS the earliest dirty upstream —
              instead of failing in place.
    BLOCKED — stage-1 BLOCKED (evaluator crashed) OR the recycle loop cap is hit
              (we have recycled this transition too many times → escalate to a
              human; never recycle forever).

This is the "gate returns to an earlier phase; cap the loop" DoD of TA.3.

STATE MACHINE
=============
States: PASS · FAIL · RECYCLE(→target_phase) · BLOCKED.

    stage1 == BLOCKED ........................................ -> BLOCKED  (crash; never a pass)
    recycle_count >= recycle_cap  AND  upstream dirty ......... -> BLOCKED  (loop cap; escalate)
    upstream dirty (earliest owner phase < N) ................ -> RECYCLE -> that phase
    stage1 in (FAILED, CONTESTED, WARNING-correctness) ....... -> FAIL    (local failure)
    stage1 PASSED  AND  no dirty upstream .................... -> PASS

Precedence is deliberate: BLOCKED (crash) and the loop cap dominate, then
RECYCLE (upstream is the real cause), then the local FAIL, then PASS. A crash is
NEVER a pass and the cap NEVER lets the loop run unbounded — both are the U16
"no false green" invariant carried forward.

RECYCLE-TARGET SELECTION (via dirty_set)
========================================
Every build-graph node maps to the phase that OWNS it (`_NODE_PHASE`):
  D-02 -> 1 (Analysis) · D-19/matrix -> 2 (Design) · task-breakdown/code -> 3
  (Implementation) · gate -> the gate's own phase (not a recycle source).
The recycle target is the **lowest** owning-phase number among the dirty nodes
that sit strictly upstream of the current phase N (k = N − target ≥ 1). Lowest =
earliest = the root cause; fixing an early phase re-dirties everything below it,
so recycling to the earliest dirty phase is the only choice that can converge.

LOOP CAP
========
A recycle is only meaningful a bounded number of times: if phase N keeps
recycling to the same earlier phase and the upstream stays dirty, something is
structurally stuck (the two phases disagree, or the fix never lands). After
`--recycle-cap` recycles of THIS transition (count carried in by the caller /
read from the gate log), the state-machine refuses to recycle again and returns
BLOCKED with `reason: recycle_cap_exceeded` so a human breaks the loop. This is
the seam TA.8's circuit-breaker extends (blow-appetite → re-slice/defer/kill).

WIRED-IN LATER WAVES (same file, sequential)
============================================
  * TA.4 (2-tier exit-criteria: must-knockout / should-scorecard) is computed in
    the companion `gate-tier.py` and threaded through `compose_outcome` via the
    optional `tier` arg — the tier verdict's `knockout` status is what feeds
    `stage1_status`, and the full tier dict is attached to the output `tier`
    field (was reserved). The tiering happens BEFORE this state-machine; here the
    stage-1 verdict is already-final.
  * TA.8 (circuit-breaker) extends the loop-cap branch: when the recycle cap is
    hit (appetite blown), the outcome is still BLOCKED but now carries a
    `circuit_breaker` decision surface — re-slice / defer / kill — that the gate
    RECOMMENDS to the user (it never auto-acts). Built on the
    `recycle_cap_exceeded` reason + `recycle_count`/`recycle_cap` seam.
  * TA.2 reconcile primitive (machine-floor + semantic-ceiling, CONTESTED) lives
    in hbc-shared; this module uses the build-graph `dirty_set` it exposes and
    does NOT re-implement reconcile.

Stdlib-only; deterministic (no time/random); None-safe. Run with `python`.
"""
from __future__ import annotations

import argparse
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

# --- shared lib bootstrap (parents[2] -> repo's src/) --- the TA.1 build-graph
# kernel lives next to hbc_validation; load_corpus + dirty_set give us stage 2.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hbc-shared" / "lib"))
try:
    from hbc_buildgraph import load_corpus  # noqa: E402
    _HAVE_GRAPH = True
except ModuleNotFoundError:
    _HAVE_GRAPH = False


# Which phase OWNS each build-graph node — i.e. which phase must be re-entered to
# fix it. Used only to pick the recycle target; the build-graph itself is
# phase-agnostic. `gate` is excluded: a gate report is an OUTPUT of evaluating a
# phase, never an upstream a later phase derives from, so it never selects a
# recycle target on its own.
_NODE_PHASE: dict[str, int] = {
    "D-02": 1,             # Requirements — Analysis
    "D-19": 2,             # ER diagram / data model — Design
    "matrix": 2,           # traceability matrix — Design/Test-Design
    "task-breakdown": 3,   # task breakdown — Implementation
    "code": 3,             # ground-truth code — Implementation
}

DEFAULT_RECYCLE_CAP = 3


def _node_phase(node_id: str) -> int | None:
    """Owning phase for a dirty node id, or None if the node doesn't map to a
    recyclable phase (e.g. the gate node, or an unknown id — None-safe)."""
    return _NODE_PHASE.get(node_id)


def select_recycle_target(dirty: dict, current_phase: int) -> dict | None:
    """Pick the RECYCLE target phase from a build-graph dirty-set.

    Returns ``{target_phase, k, node, owning_phase, all_dirty_upstream}`` for the
    EARLIEST (lowest-numbered) phase that owns a dirty node strictly upstream of
    ``current_phase`` (owning_phase < current_phase). Returns None when nothing
    upstream is dirty — then the failure (if any) is local and the caller emits a
    flat FAIL rather than a recycle.

    Earliest-wins is load-bearing: a dirty Phase-1 artifact re-dirties every
    derived artifact below it, so recycling to anything later than the earliest
    dirty phase would leave the root cause in place and the loop could never
    converge. Deterministic: ties broken by node id.
    """
    candidates = []
    for node_id in sorted(dirty):
        owning = _node_phase(node_id)
        if owning is None:
            continue
        if owning < current_phase:
            candidates.append((owning, node_id))
    if not candidates:
        return None
    candidates.sort()  # (phase, node_id) — lowest phase, then node id
    target_phase, node = candidates[0]
    return {
        "target_phase": target_phase,
        "k": current_phase - target_phase,
        "node": node,
        "owning_phase": target_phase,
        "all_dirty_upstream": [n for _, n in candidates],
    }


def circuit_breaker(
    recycle: dict,
    current_phase: int,
    recycle_count: int,
    recycle_cap: int,
) -> dict:
    """TA.8 — the circuit-breaker decision surface for a blown-appetite gate.

    When the recycle loop-cap is hit the feature has *blown its appetite*: it keeps
    being recycled to the same earlier phase yet the upstream stays dirty — the loop
    is structurally stuck. A flat BLOCKED would just dead-end the user. Instead this
    surfaces a STRUCTURED escalation of three outcomes the user can pick from:

      * re-slice — break the feature into smaller pieces; the stuck upstream likely
        spans too much scope, so a smaller slice can converge where the whole can't.
      * defer    — park the feature (the upstream churn is real but not now); take it
        out of the active loop so it stops burning recycles.
      * kill     — stop work on it; the repeated failure says the cost has exceeded
        the appetite and it is not worth finishing.

    This is a RECOMMENDATION, not an action: the gate offers the options + a default
    leaning, and the USER decides (the L·needs-design "machine surfaces, human
    decides" rule). Deterministic — no time/random; the recommendation is a pure
    function of the recycle/loop state.
    """
    node = recycle.get("node")
    target = recycle.get("target_phase")
    # A heuristic, non-binding default leaning so the surface isn't a blank menu:
    # the broader the dirty upstream (more nodes), the more re-slicing helps; a
    # single stubborn node that keeps failing leans toward defer/kill.
    dirty_breadth = len(recycle.get("all_dirty_upstream", []) or [node])
    recommended = "re-slice" if dirty_breadth > 1 else "defer"
    return {
        "triggered": True,
        "reason": "appetite_blown",
        "recycle_count": recycle_count,
        "recycle_cap": recycle_cap,
        "stuck_transition": {"from_phase": current_phase, "to_phase": target, "node": node},
        "options": [
            {"action": "re-slice",
             "what": f"Break the feature down so the stuck upstream (phase {target}, "
                     f"'{node}') is split into smaller, independently-convergent slices."},
            {"action": "defer",
             "what": "Park the feature out of the active loop; the upstream churn is "
                     "real but does not have to be resolved now — stop burning recycles."},
            {"action": "kill",
             "what": "Stop work on the feature; repeated failure says the cost has "
                     "exceeded the appetite and it is not worth finishing."},
        ],
        "recommended": recommended,
        "decision": "user",  # the gate recommends; the user decides — never auto-acted.
    }


def compose_outcome(
    stage1_status: str,
    dirty: dict,
    current_phase: int,
    recycle_count: int,
    recycle_cap: int,
    tier: dict | None = None,
) -> dict:
    """The TA.3 two-stage outcome state-machine (+ TA.4 tier / TA.8 circuit-breaker).

    Composes stage-1 (the U16 checklist verdict, passed in as ``stage1_status`` —
    in the wired flow this is the TA.4 tier KNOCKOUT status) with stage-2 (the
    build-graph ``dirty_set``) into a single outcome. Pure function of its inputs —
    deterministic and unit-testable, no I/O.

    Precedence (see module docstring): BLOCKED(crash) → loop-cap(+circuit-breaker)
    → RECYCLE → FAIL(local) → PASS.

    TA.4: ``tier`` is the full tier-aware verdict (from ``gate-tier.py``); it is
    attached to the output ``tier`` field for the report. The must/should tiering of
    ``stage1_status`` happened BEFORE this call — here the verdict is already-final
    and a SHOULD-fail can never flip a PASS to FAIL (the knockout already decided it).
    """
    s1 = (stage1_status or "").upper()
    recycle = select_recycle_target(dirty, current_phase)

    base = {
        "stage1_status": s1,
        "stage2_dirty": {k: dirty[k] for k in sorted(dirty)} if dirty else {},
        "current_phase": current_phase,
        "recycle_count": recycle_count,
        "recycle_cap": recycle_cap,
        "tier": tier,  # TA.4 tier-aware verdict (None when not wired)
    }

    # 1. crash dominates — a BLOCKED stage-1 is never anything but BLOCKED.
    if s1 == "BLOCKED":
        return {**base, "outcome": "BLOCKED", "reason": "stage1_blocked",
                "evidence": "Stage-1 evaluator BLOCKED (crash/un-runnable) — never a pass."}

    # 2. loop cap — if an upstream is dirty but we've already recycled this
    #    transition recycle_cap times, refuse to recycle again. Escalate to BLOCKED
    #    AND (TA.8) surface the circuit-breaker re-slice/defer/kill decision surface
    #    rather than a silent dead-end.
    if recycle is not None and recycle_count >= recycle_cap:
        return {**base, "outcome": "BLOCKED", "reason": "recycle_cap_exceeded",
                "recycle_target": recycle,
                "circuit_breaker": circuit_breaker(recycle, current_phase,
                                                   recycle_count, recycle_cap),
                "evidence": f"Upstream still dirty after {recycle_count} recycle(s) "
                            f"(cap {recycle_cap}). Appetite blown — gate recommends "
                            f"re-slice/defer/kill (user decides); never recycle forever."}

    # 3. upstream dirty → RECYCLE to the earliest owning phase, not a flat FAIL.
    if recycle is not None:
        return {**base, "outcome": "RECYCLE", "reason": "upstream_dirty",
                "recycle_target": recycle,
                "evidence": f"Recycle to phase {recycle['target_phase']} (k={recycle['k']}): "
                            f"upstream '{recycle['node']}' is dirty/stale — fix belongs "
                            f"there, not in phase {current_phase}."}

    # 4. no upstream dirty: local failure stays a FAIL (stage-1 owns the verdict).
    if s1 in ("FAILED", "FAIL", "CONTESTED", "WARNING"):
        return {**base, "outcome": "FAIL", "reason": f"stage1_{s1.lower()}",
                "evidence": f"Stage-1 {s1} with no dirty upstream — local failure, fix in place."}

    # 5. stage-1 clean AND nothing upstream dirty → PASS.
    if s1 in ("PASSED", "PASS", "PASSED_PENDING_SIGNOFF"):
        return {**base, "outcome": "PASS", "reason": "stage1_passed_clean_upstream",
                "evidence": "Stage-1 PASSED and no dirty upstream — both stages green."}

    # Unknown stage-1 verdict (e.g. PENDING_LLM reaching here) — never silently
    # pass; treat as a local FAIL the caller must resolve.
    return {**base, "outcome": "FAIL", "reason": f"stage1_unresolved_{s1.lower()}",
            "evidence": f"Stage-1 verdict {s1!r} is not a final pass/fail and no upstream "
                        "is dirty — treated as FAIL (never an auto-pass)."}


def run(
    feature_dir: str,
    current_phase: int,
    stage1_status: str,
    recycle_count: int,
    recycle_cap: int,
    tier: dict | None = None,
) -> dict:
    """Stage 2 (build-graph dirty-set over the feature) + the state-machine.

    A missing/unreadable feature dir, or an un-importable build-graph kernel, is
    treated as an EMPTY dirty-set with a `stage2_degraded` note — stage 2 cannot
    INVENT a recycle, but it also must not crash the gate. Crash-safety proper is
    the caller's last-resort catch (parity with the U16 evaluator).

    ``tier`` (TA.4) is the optional tier-aware verdict from ``gate-tier.py``; it is
    threaded into the outcome's ``tier`` field. When supplied, its ``knockout``
    status is the authoritative ``stage1_status`` the caller should pass in.
    """
    degraded = None
    dirty: dict = {}
    if not _HAVE_GRAPH:
        degraded = "build-graph kernel (hbc_buildgraph) not importable; stage-2 skipped"
    else:
        try:
            g = load_corpus(Path(feature_dir))
            dirty = g.dirty_set()
        except Exception as exc:  # noqa: BLE001 — stage-2 best-effort, never crash the gate
            degraded = f"stage-2 build-graph failed: {type(exc).__name__}: {exc}"

    outcome = compose_outcome(stage1_status, dirty, current_phase, recycle_count,
                              recycle_cap, tier=tier)
    if degraded:
        outcome["stage2_degraded"] = degraded
    return outcome


def main():
    p = argparse.ArgumentParser(description="TA.3 gate two-stage verify + RECYCLE outcome.")
    p.add_argument("--feature-dir", required=True,
                   help="Feature directory the build-graph loads (stage 2).")
    p.add_argument("--phase", type=int, required=True, help="Current phase number (1-4).")
    p.add_argument("--stage1-status", default="",
                   help="Stage-1 verdict from evaluate-gate-checklist.py "
                        "(PASSED/FAILED/CONTESTED/BLOCKED/...). Required UNLESS --tier-json "
                        "is given, in which case the tier knockout status is used.")
    p.add_argument("--recycle-count", type=int, default=0,
                   help="How many times THIS transition has already recycled "
                        "(read from the gate log; default 0).")
    p.add_argument("--recycle-cap", type=int, default=DEFAULT_RECYCLE_CAP,
                   help=f"Max recycles before escalating to BLOCKED (default {DEFAULT_RECYCLE_CAP}).")
    p.add_argument("--tier-json",
                   help="Optional TA.4 tier verdict JSON (from gate-tier.py); attached "
                        "to the `tier` field. If given and --stage1-status is omitted, "
                        "its knockout status is used as the stage-1 verdict.")
    p.add_argument("-o", "--output", help="Output file (default stdout).")
    args = p.parse_args()

    if not args.stage1_status and not args.tier_json:
        p.error("one of --stage1-status or --tier-json is required")

    tier = None
    stage1 = args.stage1_status
    if args.tier_json:
        tier = json.loads(Path(args.tier_json).read_text(encoding="utf-8"))
        if not stage1:
            # Knockout status (PASSED/FAILED) is the authoritative stage-1 verdict;
            # a must-blocked tier propagates as BLOCKED.
            stage1 = (tier.get("tier_verdict") if tier.get("tier_verdict") == "BLOCKED"
                      else tier.get("knockout", {}).get("status", ""))

    result = run(args.feature_dir, args.phase, stage1,
                 args.recycle_count, args.recycle_cap, tier=tier)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Outcome written to {args.output}", file=sys.stderr)
    else:
        print(text)

    # Exit non-zero on anything but a clean PASS — CI never reads exit 0 as a
    # clean gate on a RECYCLE / FAIL / BLOCKED outcome.
    sys.exit(0 if result.get("outcome") == "PASS" else 1)


if __name__ == "__main__":
    # Crash → BLOCKED, never a silent pass (parity with evaluate-gate-checklist.py).
    try:
        main()
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 — last-resort: must not become a pass
        import traceback
        print(json.dumps({
            "outcome": "BLOCKED",
            "reason": "outcome_evaluator_crashed",
            "evidence": f"{type(exc).__name__}: {exc}",
        }, ensure_ascii=False))
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)
