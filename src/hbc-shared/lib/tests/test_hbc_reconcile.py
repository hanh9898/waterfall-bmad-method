#!/usr/bin/env python3
"""Tests for the reconcile primitive (TA.2) — hbc_reconcile.py.

Proves: machine-floor RED → FAIL + invariant flag set; floor-GREEN → semantic
`pending` (NOT auto-pass); the invariant-FAIL cannot be downgraded by ANY path
(frozen dataclass + waiver-refusal + computed `passed`); reuse-not-reimplement of
TA.1 ground_truth_drift / shared model_drift / version_coherence; and the eval on
BOTH corpora (broken TD.0 → invariant-FAIL; clean corpus → no false-FAIL).
Run via pytest or `python test_hbc_reconcile.py`.
"""
import dataclasses
import json
import sys
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_LIB))

from hbc_buildgraph import BuildGraph, Node, load_corpus, feature_dirs  # noqa: E402
from hbc_reconcile import (  # noqa: E402
    FLOOR_FAIL,
    FLOOR_PASS,
    SEMANTIC_NEEDS_REVIEW,
    ReconcileVerdict,
    apply_waiver,
    reconcile,
    reconcile_pair,
    reconcile_report,
)

_REPO = _LIB.parents[2]
BROKEN = _REPO / "process-review" / "fixtures" / "resource-plan-billable"
CLEAN = _REPO / "process-review" / "spikes" / "ta0" / "corpus-clean"


# --- helpers ---------------------------------------------------------------

def _drift_graph():
    """design declares new.model; code only defines old.model → model drift."""
    g = BuildGraph()
    g.add(Node(id="code", kind="code", text="class P:\n    _name = 'old.model'\n"))
    g.add(Node(id="D-19", kind="doc",
               text="Physical name (Tên vật lý): `new.model`\n", reconcile_to="code"))
    return g


def _clean_pair_graph():
    g = BuildGraph()
    g.add(Node(id="code", kind="code", text="_name = 'm.model'\n"))
    g.add(Node(id="D-19", kind="doc",
               text="Physical name: `m.model`\n", reconcile_to="code"))
    return g


# --- machine-floor RED → FAIL + invariant ----------------------------------

def test_model_drift_floor_fail_and_invariant():
    v = reconcile(_drift_graph(), "D-19")
    assert v.machine_floor == FLOOR_FAIL
    assert v.invariant_fail is True
    assert v.passed is False
    # evidence carries the exact drift IDs (the floor's facts, for the LLM to cite)
    drift_reason = next(r for r in v.floor_reasons if r["check"] == "model_drift")
    assert "new.model" in drift_reason["evidence"]["design_only"]


def test_staleness_floor_fail():
    """A design node whose recorded upstream version is stale → staleness floor RED."""
    g = BuildGraph()
    g.add(Node(id="D-02", kind="doc", text="r", version="2.3"))
    g.add(Node(id="matrix", kind="matrix", text="m", sources={"D-02": "v1.0"}))  # stale
    v = reconcile(g, "matrix", matrix_coverage=False)
    assert v.machine_floor == FLOOR_FAIL and v.invariant_fail
    assert any(r["check"] == "staleness" for r in v.floor_reasons)


def test_coverage_floor_fail_on_matrix():
    d02 = "## Requirements\n\n| REQ ID | d |\n|---|---|\n| REQ-F-001 | x |\n| REQ-F-002 | y |\n"
    mtx = ("| req_id | design_ref | code_ref | test_ref |\n|---|---|---|---|\n"
           "| REQ-F-001 | E | c.py | TC-1 |\n")  # REQ-F-002 missing
    g = BuildGraph()
    g.add(Node(id="D-02", kind="doc", text=d02, version="1.0"))
    g.add(Node(id="matrix", kind="matrix", text=mtx, sources={"D-02": None}))
    # neutralize staleness so we isolate the coverage check
    g.get("matrix").sources = {"D-02": g.get("D-02").hash}
    v = reconcile(g, "matrix")
    assert v.machine_floor == FLOOR_FAIL
    cov = next(r for r in v.floor_reasons if r["check"] == "coverage")
    assert "REQ-F-002" in cov["evidence"]["missing_reqs"]


def test_version_coherence_floor_fail_when_citing_texts_given():
    g = BuildGraph()
    g.add(Node(id="code", kind="code", text="_name = 'm.model'\n"))
    g.add(Node(id="D-02", kind="doc", text="r", version="2.3"))
    # downstream doc cites D-02 v2.2 while D-02 is v2.3
    v = reconcile(g, "D-02", citing_texts={"D-26": "traces D-02 (v2.2)"})
    assert v.machine_floor == FLOOR_FAIL
    assert any(r["check"] == "version_coherence" for r in v.floor_reasons)


# --- machine-floor GREEN → semantic pending (NOT auto-pass) -----------------

def test_floor_green_is_semantic_pending_not_passed():
    v = reconcile(_clean_pair_graph(), "D-19")
    assert v.machine_floor == FLOOR_PASS
    assert v.invariant_fail is False
    assert v.semantic == SEMANTIC_NEEDS_REVIEW  # owed, not granted
    assert v.passed is False, "a green floor is NOT a passed reconcile until the LLM judges"


def test_floor_green_passes_only_after_semantic_review():
    v = reconcile(_clean_pair_graph(), "D-19")
    waived = apply_waiver(v, semantic="passed")
    assert waived.passed is True
    assert waived.semantic == "passed"


# --- THE INVARIANT: a machine-floor RED cannot be downgraded by any path ----

def test_invariant_fail_cannot_be_downgraded_by_waiver():
    v = reconcile(_drift_graph(), "D-19")
    waived = apply_waiver(v, semantic="passed")  # caller TRIES to wave away the drift
    assert waived.machine_floor == FLOOR_FAIL, "waiver must NOT flip a floor fail"
    assert waived.invariant_fail is True
    assert waived.passed is False
    assert waived.waiver_refused is True, "the refused attempt must be on the audit trail"
    assert waived.semantic != "passed"


def test_invariant_fail_verdict_is_frozen():
    """No caller can reassign a field to soften the floor — the dataclass is frozen."""
    v = reconcile(_drift_graph(), "D-19")
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.machine_floor = FLOOR_PASS  # type: ignore[misc]


def test_passed_is_computed_cannot_be_true_while_floor_fails():
    """`passed` is a property derived from machine_floor — there is no stored flag a
    caller could set True. Construct a FAIL with a (nonsensical) 'passed' semantic and
    confirm `passed` is still False."""
    v = ReconcileVerdict(machine_floor=FLOOR_FAIL, semantic="passed")
    assert v.passed is False
    assert v.invariant_fail is True


def test_waiver_on_green_floor_does_not_set_refused():
    v = reconcile(_clean_pair_graph(), "D-19")
    waived = apply_waiver(v, semantic="passed")
    assert waived.waiver_refused is False


# --- reuse, not reimplement ------------------------------------------------

def test_reuses_ground_truth_drift_signal(monkeypatch):
    """The floor's model-drift must come THROUGH the graph's ground_truth_drift (TA.1),
    not a private re-implementation — patch it and the floor must follow."""
    g = _clean_pair_graph()  # would normally be floor-green
    import hbc_buildgraph
    orig = hbc_buildgraph.BuildGraph.ground_truth_drift

    def fake(self, **kw):
        return [{"design_node": "D-19", "ground_truth_node": "code",
                 "design_only": ["injected.model"], "code_only": [], "drift": True}]

    monkeypatch.setattr(hbc_buildgraph.BuildGraph, "ground_truth_drift", fake)
    try:
        v = reconcile(g, "D-19")
        assert v.machine_floor == FLOOR_FAIL  # follows the patched TA.1 signal
        assert "injected.model" in v.floor_reasons[0]["evidence"]["design_only"]
    finally:
        monkeypatch.setattr(hbc_buildgraph.BuildGraph, "ground_truth_drift", orig)


def test_reconcile_pair_uses_model_drift():
    fail = reconcile_pair("Physical name: `new.model`", "_name = 'old.model'")
    assert fail.machine_floor == FLOOR_FAIL and fail.invariant_fail
    ok = reconcile_pair("Physical name: `m.model`", "_name = 'm.model'")
    assert ok.machine_floor == FLOOR_PASS and ok.semantic == SEMANTIC_NEEDS_REVIEW


# --- edge / none-safety / determinism --------------------------------------

def test_unknown_node_raises():
    with pytest.raises(ValueError):
        reconcile(BuildGraph(), "ghost")


def test_design_node_without_ground_truth_still_runs_floor():
    """A design node with no reconcile_to skips model-drift but still asserts the floor
    it CAN (staleness/coverage); a clean such node is floor-green pending."""
    g = BuildGraph()
    g.add(Node(id="D-02", kind="doc", text="r", version="1.0"))
    v = reconcile(g, "D-02")
    assert v.machine_floor == FLOOR_PASS
    assert v.ground_truth_node is None


def test_reconcile_deterministic():
    g = _drift_graph()
    a = json.dumps(reconcile(g, "D-19").to_dict(), sort_keys=True)
    b = json.dumps(reconcile(g, "D-19").to_dict(), sort_keys=True)
    assert a == b


def test_extra_token_fields_only_when_present_in_design():
    """An extra token NOT in the design text must not manufacture drift (kernel rule)."""
    g = _clean_pair_graph()
    v = reconcile(g, "D-19", extra_token_fields=("totally.unrelated",))
    assert v.machine_floor == FLOOR_PASS  # token absent from design → no false drift


# --- eval on the corpora ----------------------------------------------------

@pytest.mark.skipif(not BROKEN.is_dir(), reason="TD.0 fixture not present")
def test_broken_fixture_reconciles_to_invariant_fail():
    g = load_corpus(BROKEN)
    v = reconcile(g, "D-19")  # D-19 ↔ code: the RCA drift
    assert v.machine_floor == FLOOR_FAIL
    assert v.invariant_fail is True
    drift = next(r for r in v.floor_reasons if r["check"] == "model_drift")
    assert "resource.plan.request" in drift["evidence"]["design_only"]
    # and it cannot be waived to a pass
    assert apply_waiver(v, semantic="passed").machine_floor == FLOOR_FAIL


@pytest.mark.skipif(not BROKEN.is_dir(), reason="TD.0 fixture not present")
def test_broken_fixture_matrix_coverage_invariant_fail():
    g = load_corpus(BROKEN)
    v = reconcile(g, "matrix")
    assert v.invariant_fail is True
    cov = next(r for r in v.floor_reasons if r["check"] == "coverage")
    nums = {m[-3:] for m in cov["evidence"]["missing_reqs"]}
    assert {"040", "041", "042"} <= nums


@pytest.mark.skipif(not BROKEN.is_dir(), reason="TD.0 fixture not present")
def test_broken_fixture_report_flags_invariant():
    rep = reconcile_report(load_corpus(BROKEN))
    assert rep["any_invariant_fail"] is True
    assert rep["all_floor_green"] is False


@pytest.mark.skipif(not CLEAN.is_dir(), reason="clean corpus not present")
def test_clean_corpus_no_false_fail():
    feats = feature_dirs(CLEAN)
    assert len(feats) >= 2, "clean corpus must be multi-feature (else proof is vacuous)"
    for fd in feats:
        g = load_corpus(fd)
        rep = reconcile_report(g)
        assert rep["any_invariant_fail"] is False, f"{fd.name}: clean corpus must NOT invariant-fail"
        assert rep["all_floor_green"] is True, f"{fd.name}: every reconcile floor must be green"
        # green floor still leaves the semantic ceiling owed — not auto-passed
        assert rep["semantic_pending"], f"{fd.name}: a green floor is pending, not passed"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
