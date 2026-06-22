#!/usr/bin/env python3
"""HBC reconcile primitive (TA.2) — the machine-floor + semantic-ceiling verdict.

WHAT THIS IS
============
``reconcile(...)`` is the ONE primitive every consistency seam reuses (gate /verify,
v_pair, readiness, acceptance). Given a *design node* and the *ground-truth node* it
reconciles against (both from the TA.1 build-graph), it answers the only question the
machine is allowed to answer about that pair — "are they FACTUALLY in sync?" — and
separates that hard floor from the judgement the LLM still owes.

The redesign (`hbc-buildgraph-redesign-2026-06-21.md` §3.2) splits a reconcile into
two deliberately-separate layers:

    ① MACHINE FLOOR (Python, deterministic): parse design, parse ground-truth,
       set-diff / hash / coverage → facts. This is the gate's HARD floor.
    ② SEMANTIC CEILING (LLM, adversarial): "is a machine-GREEN reconcile actually
       MEANINGFUL?" (rename-vs-real-divergence, intent match, deliberate denorm).
       NOT decided in Python — exposed as an honest `pending` state with a rubric hook.

THE LOAD-BEARING RULE — INVARIANT FAIL (TA.2 DoD)
=================================================
If ANY machine-floor check is RED, the verdict's ``machine_floor == "FAIL"`` and
``invariant_fail is True``, and **no caller can downgrade it**. This is the direct
remediation of the RCA failure (a model that drifted from its design still earned a
"gate PASSED" via a manual / lenient / waiver override). The invariant is enforced
structurally, not by convention:

  * ``ReconcileVerdict`` is FROZEN (``@dataclass(frozen=True)``) — its fields cannot be
    reassigned after construction (``verdict.machine_floor = "pass"`` raises).
  * The ONLY mutation path, ``apply_waiver(...)``, REFUSES on an invariant fail: it
    returns the verdict unchanged and records ``waiver_refused``. A machine-floor RED
    can never become a pass; a waiver may only annotate a machine-floor-GREEN verdict's
    semantic ceiling (which is a judgement, not a fact).
  * ``passed`` is a computed property, not a stored flag, so it can NEVER read True
    while ``machine_floor == "FAIL"`` regardless of what any caller sets.

BOUNDARY (F-3): the invariant guarantees no caller can **downgrade a verdict that
came from** ``reconcile()`` / ``reconcile_report()``. It does NOT (and a Python
primitive cannot) stop a caller from **fabricating** a passing verdict from scratch
(``ReconcileVerdict(machine_floor=FLOOR_PASS, semantic="passed")``) or via
``object.__setattr__`` — that is forgery, not a downgrade path. The CONTRACT for every
consumer (the gate TA.3, coverage TA.5, v_pair TA.6) is therefore: **obtain the verdict
by calling ``reconcile()``/``reconcile_report()`` — never hand-construct one.** Gate
reviews must assert provenance, not just read ``passed``.

A machine-floor RED is a FACT (a hash mismatch, a model the design declares that code
never defines, a REQ with no matrix row). Facts are not negotiable; that is the whole
point of pushing them to the machine floor (CLAUDE.md 3-layer split). The semantic
ceiling is the *opposite* — a machine-floor-GREEN reconcile is NOT auto-passed; it is
``pending`` until the LLM review layer judges it, because "names differ but mean the
same thing" / "this divergence is intentional" is meaning, not structure.

SCOPE (TA.2 only — additive, see CLAUDE.md "Validator architecture")
====================================================================
This module REUSES TA.1's ``ground_truth_drift`` + the shared ``model_drift`` /
``version_coherence`` primitives for the floor checks — it does NOT reimplement them.
It builds the *verdict ladder* the kernel deferred (hbc_buildgraph §3.2 note). It does
NOT build the gate state-machine (TA.3), the 100%-rule coverage engine (TA.5), or the
v_pair edge enforcement (TA.6) — those CALL this primitive. stdlib-only; deterministic
(identical graph state → identical verdict); same-dir import like its siblings.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import sys

# Shared kernel + leaf primitives — reuse, never duplicate (CLAUDE.md). Same-dir
# import; the bootstrap also lets a consumer run this file directly.
_LIB_DIR = Path(__file__).resolve().parent
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from hbc_buildgraph import BuildGraph, Node  # noqa: E402
from hbc_validation import (  # noqa: E402
    SEMANTIC_NA,
    SEMANTIC_PENDING,
    model_drift,
    version_coherence,
)

# Machine-floor verdict states. These describe FACTS the machine owns.
FLOOR_PASS = "pass"   # every machine-floor check is green
FLOOR_FAIL = "FAIL"   # ≥1 machine-floor check is RED — INVARIANT, never downgradable

# Semantic-ceiling state owed when (and only when) the floor is green. Re-exported
# from hbc_validation so callers import the one canonical set of states.
SEMANTIC_NEEDS_REVIEW = SEMANTIC_PENDING  # alias for the rubric-hook name in §3.2


@dataclass(frozen=True)
class ReconcileVerdict:
    """The honest verdict of a single ``reconcile(design, ground_truth)``.

    FROZEN on purpose: once the machine floor has spoken, no caller may reassign a
    field to soften it (``verdict.machine_floor = FLOOR_PASS`` raises FrozenInstance
    error). The only sanctioned transform is ``apply_waiver`` (below), which itself
    refuses to touch an invariant fail. ``passed`` is computed, never stored.

    Fields
    ------
    machine_floor : "pass" | "FAIL"
        The deterministic floor. "FAIL" iff ≥1 floor check is red.
    floor_reasons : list[dict]
        One entry per red floor check: ``{check, detail, evidence}``. Empty on pass.
        The machine's evidence — IDs/counts the LLM ceiling MUST cite (B6-1/B6-2),
        never re-count.
    semantic : "n/a" | "pending" | "passed"
        The ceiling. On a floor FAIL this is "n/a" (the LLM is not asked to judge a
        thing the machine already rejected). On a floor pass it starts "pending" —
        a green floor is NOT a green reconcile until the LLM review runs.
    invariant_fail : bool
        True iff ``machine_floor == FLOOR_FAIL``. The explicit, queryable flag a gate
        / waiver / lenient path checks to know it MUST NOT downgrade.
    design_node, ground_truth_node : str | None
        The pair this verdict is about (for traceability in a multi-node report).
    rubric : str
        The semantic-review rubric hook the LLM ceiling applies (B6 facet-split).
    waiver_refused : bool
        True iff an ``apply_waiver`` call was rejected because the floor failed — the
        audit trail that an attempt to downgrade an invariant fail happened and lost.
    """

    machine_floor: str
    floor_reasons: list = field(default_factory=list)
    semantic: str = SEMANTIC_NA
    design_node: str | None = None
    ground_truth_node: str | None = None
    rubric: str = "hbc-shared/references/semantic-review-rubric.md"
    waiver_refused: bool = False

    @property
    def invariant_fail(self) -> bool:
        """The load-bearing flag: a machine-floor RED that no path may downgrade.

        Computed from ``machine_floor`` (not stored) so it cannot be set False while
        the floor is FAIL."""
        return self.machine_floor == FLOOR_FAIL

    @property
    def passed(self) -> bool:
        """A reconcile is PASSED only when the floor is green AND the semantic ceiling
        is no longer owed (``passed``). A floor FAIL can never read passed; a floor-
        green-but-``pending`` reconcile is NOT passed (honest: review still owed)."""
        return self.machine_floor == FLOOR_PASS and self.semantic == "passed"

    def to_dict(self) -> dict:
        return {
            "machine_floor": self.machine_floor,
            "floor_reasons": list(self.floor_reasons),
            "semantic": self.semantic,
            "invariant_fail": self.invariant_fail,
            "passed": self.passed,
            "design_node": self.design_node,
            "ground_truth_node": self.ground_truth_node,
            "rubric": self.rubric,
            "waiver_refused": self.waiver_refused,
        }


def apply_waiver(verdict: ReconcileVerdict, *, semantic: str) -> ReconcileVerdict:
    """The ONLY sanctioned mutation of a verdict — and it refuses to downgrade a fail.

    A waiver / sign-off / lenient path may record an LLM/human *semantic-ceiling*
    judgement on a machine-floor-GREEN reconcile (e.g. "rename, not divergence →
    semantic=passed"). It may NEVER soften a machine-floor RED:

      * If ``verdict.invariant_fail`` → the floor RED is a FACT; the waiver is REFUSED.
        The original verdict is returned UNCHANGED except ``waiver_refused=True`` (the
        audit trail), so a caller that tries to wave away a drift is recorded as having
        tried and lost. ``machine_floor`` stays "FAIL".
      * Otherwise → the ``semantic`` field is updated (the judgement layer's job).

    This is the structural guarantee that the TA.3 gate / TA.7 rebaseline / any lenient
    flag cannot turn a machine-floor RED into a pass: there is no other write path, and
    this one short-circuits on the invariant.
    """
    if verdict.invariant_fail:
        # FACT stands. Record the refused attempt; do not touch the floor or semantic.
        return replace(verdict, waiver_refused=True)
    return replace(verdict, semantic=semantic)


def reconcile(
    graph: BuildGraph,
    design_node_id: str,
    *,
    extra_token_fields=(),
    matrix_coverage: bool = True,
    citing_texts: dict | None = None,
) -> ReconcileVerdict:
    """Reconcile one design node against its ground-truth node, on a TA.1 build-graph.

    The machine floor runs three deterministic checks, each REUSING an existing
    primitive (no reimplementation):

      1. MODEL DRIFT (``ground_truth_drift`` → ``model_drift``): a model the design
         declares but code never defines, or a persistent model in code the design
         never mentions. The RCA drift (design moved to Request+Snapshot, code stayed).
      2. STALENESS (``graph.dirty_set``): the design node's recorded source token no
         longer matches an upstream's current hash/version, OR an upstream is dirty.
         A node reconciled against a moved upstream is stale by fact.
      3. COVERAGE (``graph.missing_edges``, opt-out via ``matrix_coverage=False``):
         a REQ defined in D-02 with no matrix row — only meaningful when the design
         node IS the matrix (the "39/39 green but 040/041/042 never added" failure).

    Optionally, ``citing_texts`` ({label: text}) feeds a VERSION-COHERENCE floor check
    (``version_coherence``) — a downstream doc citing a stale version of the design.
    Off by default (the kernel loader rarely has the citing-doc set wired); a caller
    that has it (readiness, gate) passes it in.

    Any red check → ``machine_floor=FLOOR_FAIL`` + ``invariant_fail=True`` (the
    invariant). All-green floor → ``semantic=pending`` (NOT auto-pass — the ceiling is
    owed). A design node with no ``reconcile_to`` ground-truth still runs staleness +
    coverage (the floor it CAN assert); model-drift is simply skipped for it.
    """
    design = graph.get(design_node_id)
    if design is None:
        raise ValueError(f"unknown design node {design_node_id!r}")

    reasons: list[dict] = []
    gt = graph.get(design.reconcile_to) if design.reconcile_to else None
    gt_id = gt.id if (gt is not None and gt.kind == "code") else None

    # --- floor check 1: model drift against the ground-truth code node ----------
    if gt_id is not None:
        # Reuse TA.1's ground_truth_drift so the exact same drift the kernel reports
        # is what the floor judges (single source of the signal). It also applies the
        # opt-in extra_token_fields filter (kernel default empty — no feature literal).
        for d in graph.ground_truth_drift(extra_token_fields=extra_token_fields):
            if d["design_node"] != design.id:
                continue
            if d["drift"]:
                reasons.append({
                    "check": "model_drift",
                    "detail": "design declares models absent from code, or code defines "
                              "persistent models the design never mentions",
                    "evidence": {"design_only": d["design_only"], "code_only": d["code_only"]},
                })

    # --- floor check 2: staleness (recorded source token vs current upstream) ---
    dirty = graph.dirty_set()
    if design.id in dirty:
        reasons.append({
            "check": "staleness",
            "detail": "design node is stale: a recorded upstream token no longer "
                      "matches that upstream's current hash/version (or an upstream is dirty)",
            "evidence": {"dirty_reasons": list(dirty[design.id])},
        })

    # --- floor check 3: matrix coverage (only when this node is the matrix) -----
    if matrix_coverage and design.kind == "matrix":
        missing = graph.missing_edges()
        if missing:
            reasons.append({
                "check": "coverage",
                "detail": "REQs defined upstream in D-02 have no row (edge) in this matrix",
                "evidence": {"missing_reqs": list(missing)},
            })

    # --- optional floor check 4: version coherence of downstream citers ---------
    if citing_texts:
        declared = design.version
        if declared is not None:
            stale_cites = version_coherence({design.id: declared}, citing_texts)
            if stale_cites:
                reasons.append({
                    "check": "version_coherence",
                    "detail": f"a downstream doc cites a version of {design.id} other than "
                              f"its declared v{declared}",
                    "evidence": {"stale_citations": stale_cites},
                })

    if reasons:
        return ReconcileVerdict(
            machine_floor=FLOOR_FAIL,
            floor_reasons=reasons,
            semantic=SEMANTIC_NA,  # the LLM is not asked to judge a machine-rejected pair
            design_node=design.id,
            ground_truth_node=gt_id,
        )
    # Floor is green → the ceiling is OWED, not granted. pending, never auto-pass.
    return ReconcileVerdict(
        machine_floor=FLOOR_PASS,
        floor_reasons=[],
        semantic=SEMANTIC_NEEDS_REVIEW,
        design_node=design.id,
        ground_truth_node=gt_id,
    )


def reconcile_pair(
    design_text: str,
    code_text: str,
    *,
    extra_tokens=(),
    design_id: str = "design",
    code_id: str = "code",
) -> ReconcileVerdict:
    """Lightweight reconcile of a design TEXT against a code TEXT, no graph required.

    For a caller (TA.6 v_pair, a draft model-validation checkpoint) that has two blobs
    and only wants the model-drift floor. Reuses ``model_drift`` directly. Same invariant
    semantics: drift → FLOOR_FAIL + invariant; clean → semantic pending (not auto-pass).
    """
    drift = model_drift(design_text, code_text, extra_tokens=extra_tokens)
    if drift["drift"]:
        return ReconcileVerdict(
            machine_floor=FLOOR_FAIL,
            floor_reasons=[{
                "check": "model_drift",
                "detail": "design declares models absent from code, or code defines "
                          "persistent models the design never mentions",
                "evidence": {"design_only": drift["design_only"], "code_only": drift["code_only"]},
            }],
            semantic=SEMANTIC_NA,
            design_node=design_id,
            ground_truth_node=code_id,
        )
    return ReconcileVerdict(
        machine_floor=FLOOR_PASS,
        semantic=SEMANTIC_NEEDS_REVIEW,
        design_node=design_id,
        ground_truth_node=code_id,
    )


def reconcile_report(graph: BuildGraph, **kwargs) -> dict:
    """Reconcile EVERY design node that has a ground-truth ``reconcile_to`` edge, plus
    the matrix node (for coverage), and roll up. Pure derivation from current graph
    state. ``any_invariant_fail`` is the gate's hard knockout signal.
    """
    verdicts: dict[str, dict] = {}
    seen: set[str] = set()
    for n in sorted(graph.nodes.values(), key=lambda x: x.id):
        if (n.reconcile_to and graph.get(n.reconcile_to) is not None) or n.kind == "matrix":
            verdicts[n.id] = reconcile(graph, n.id, **kwargs).to_dict()
            seen.add(n.id)
    return {
        "verdicts": verdicts,
        "any_invariant_fail": any(v["invariant_fail"] for v in verdicts.values()),
        "all_floor_green": all(v["machine_floor"] == FLOOR_PASS for v in verdicts.values()) if verdicts else True,
        "semantic_pending": sorted(k for k, v in verdicts.items() if v["semantic"] == SEMANTIC_NEEDS_REVIEW),
    }
