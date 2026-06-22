#!/usr/bin/env python3
"""Tests for gate-outcome.py — TA.3 two-stage verify + RECYCLE state-machine."""

import json
import os
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_HERE = Path(__file__).resolve()
_SCRIPT = _HERE.parents[1] / "gate-outcome.py"
_REPO = _HERE.parents[4]
BROKEN = _REPO / "process-review" / "fixtures" / "resource-plan-billable"
CLEAN = _REPO / "process-review" / "spikes" / "ta0" / "corpus-clean"

_spec = spec_from_file_location("gate_outcome", str(_SCRIPT))
assert _spec is not None and _spec.loader is not None
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

compose_outcome = mod.compose_outcome
select_recycle_target = mod.select_recycle_target
reconcile_invariant_targets = mod.reconcile_invariant_targets
select_reconcile_recycle = mod.select_reconcile_recycle
circuit_breaker = mod.circuit_breaker
run = mod.run
DEFAULT_RECYCLE_CAP = mod.DEFAULT_RECYCLE_CAP


def _report(*nodes):
    """Build a reconcile_report-shaped dict. Each arg is (node_id, invariant_fail,
    reasons). Mirrors the keys gate-outcome reads — never hand-builds a verdict object.
    """
    verdicts = {}
    for nid, inv, reasons in nodes:
        verdicts[nid] = {
            "machine_floor": "FAIL" if inv else "pass",
            "invariant_fail": inv,
            "floor_reasons": reasons or [],
        }
    return {
        "verdicts": verdicts,
        "any_invariant_fail": any(n[1] for n in nodes),
        "all_floor_green": not any(n[1] for n in nodes),
        "semantic_pending": [],
    }


# --- select_recycle_target ------------------------------------------------

class TestSelectRecycleTarget:
    def test_no_dirty_returns_none(self):
        assert select_recycle_target({}, current_phase=3) is None

    def test_dirty_only_at_or_above_current_phase_is_not_upstream(self):
        # task-breakdown owns phase 3; from phase 3 it is NOT strictly upstream.
        assert select_recycle_target({"task-breakdown": ["x"]}, current_phase=3) is None

    def test_picks_earliest_owning_phase(self):
        # D-02 (phase 1) + task-breakdown (phase 3) both dirty, current phase 4.
        sel = select_recycle_target(
            {"D-02": ["a"], "task-breakdown": ["b"], "matrix": ["c"]}, current_phase=4
        )
        assert sel["target_phase"] == 1
        assert sel["node"] == "D-02"
        assert sel["k"] == 3

    def test_design_node_recycles_to_phase_2(self):
        sel = select_recycle_target({"D-19": ["stale"], "gate": ["x"]}, current_phase=3)
        assert sel["target_phase"] == 2
        assert sel["node"] == "D-19"
        assert sel["k"] == 1

    def test_gate_node_never_selects_a_target(self):
        # gate is an output, not an upstream — a dirty gate alone yields no recycle.
        assert select_recycle_target({"gate": ["x"]}, current_phase=3) is None

    def test_unknown_node_ignored_none_safe(self):
        assert select_recycle_target({"mystery-node": ["x"]}, current_phase=4) is None

    def test_tie_broken_by_node_id_deterministic(self):
        # D-19 and matrix both own phase 2 → lowest node id wins, stable.
        sel = select_recycle_target({"matrix": ["a"], "D-19": ["b"]}, current_phase=3)
        assert sel["target_phase"] == 2
        assert sel["node"] == "D-19"  # "D-19" < "matrix"
        assert sel["all_dirty_upstream"] == ["D-19", "matrix"]


# --- compose_outcome state-machine ----------------------------------------

class TestComposeOutcome:
    def test_pass_when_stage1_passed_and_no_dirty(self):
        o = compose_outcome("PASSED", {}, current_phase=2, recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "PASS"

    def test_local_fail_when_stage1_failed_no_upstream(self):
        o = compose_outcome("FAILED", {}, current_phase=2, recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "FAIL"
        assert o["reason"] == "stage1_failed"

    def test_recycle_when_upstream_dirty(self):
        # phase 3 gate, D-02 dirty upstream → recycle to phase 1.
        o = compose_outcome("FAILED", {"D-02": ["direct"]}, current_phase=3,
                            recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "RECYCLE"
        assert o["recycle_target"]["target_phase"] == 1

    def test_recycle_even_when_stage1_passed(self):
        # Stage-1 may pass locally yet an upstream drifted → still RECYCLE, not PASS.
        o = compose_outcome("PASSED", {"D-19": ["stale"]}, current_phase=3,
                            recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "RECYCLE"
        assert o["recycle_target"]["target_phase"] == 2

    def test_crash_blocks_never_passes(self):
        o = compose_outcome("BLOCKED", {}, current_phase=2, recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "BLOCKED"
        assert o["reason"] == "stage1_blocked"

    def test_crash_blocks_even_with_dirty_upstream(self):
        # A crashed stage-1 must not be re-cast as RECYCLE — crash dominates.
        o = compose_outcome("BLOCKED", {"D-02": ["x"]}, current_phase=3,
                            recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "BLOCKED"
        assert o["reason"] == "stage1_blocked"

    def test_loop_cap_blocks_no_infinite_recycle(self):
        o = compose_outcome("FAILED", {"D-02": ["x"]}, current_phase=3,
                            recycle_count=3, recycle_cap=3)
        assert o["outcome"] == "BLOCKED"
        assert o["reason"] == "recycle_cap_exceeded"
        assert o["recycle_target"]["target_phase"] == 1

    def test_recycle_allowed_below_cap(self):
        o = compose_outcome("FAILED", {"D-02": ["x"]}, current_phase=3,
                            recycle_count=2, recycle_cap=3)
        assert o["outcome"] == "RECYCLE"

    def test_cap_exceeded_takes_precedence_over_recycle(self):
        o = compose_outcome("FAILED", {"D-02": ["x"]}, current_phase=3,
                            recycle_count=5, recycle_cap=3)
        assert o["outcome"] == "BLOCKED"

    def test_contested_local_is_fail(self):
        o = compose_outcome("CONTESTED", {}, current_phase=2, recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "FAIL"

    def test_unknown_stage1_never_passes(self):
        o = compose_outcome("PENDING_LLM", {}, current_phase=2, recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "FAIL"

    def test_tier_field_reserved_for_ta4(self):
        o = compose_outcome("PASSED", {}, current_phase=2, recycle_count=0, recycle_cap=3)
        assert "tier" in o and o["tier"] is None

    def test_deterministic(self):
        a = compose_outcome("FAILED", {"D-02": ["x"], "matrix": ["y"]}, 4, 0, 3)
        b = compose_outcome("FAILED", {"D-02": ["x"], "matrix": ["y"]}, 4, 0, 3)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# --- run() — stage-2 build-graph integration ------------------------------

class TestRunStage2:
    def test_broken_fixture_recycles_not_flat_fail(self):
        # The broken TD.0 fixture has dirty {gate, task-breakdown} upstream.
        # From a Phase-4 gate, task-breakdown (phase 3) is dirty upstream → RECYCLE→3,
        # NOT a flat FAIL/PASS.
        o = run(str(BROKEN), current_phase=4, stage1_status="FAILED",
                recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "RECYCLE"
        assert o["recycle_target"]["target_phase"] == 3
        assert "task-breakdown" in o["stage2_dirty"]

    def test_broken_fixture_loop_cap_blocks(self):
        o = run(str(BROKEN), current_phase=4, stage1_status="FAILED",
                recycle_count=3, recycle_cap=3)
        assert o["outcome"] == "BLOCKED"
        assert o["reason"] == "recycle_cap_exceeded"

    def test_clean_corpus_passes_no_spurious_recycle(self):
        feats = [p for p in sorted(CLEAN.iterdir()) if p.is_dir()]
        assert feats, "clean corpus must have feature dirs"
        for fd in feats:
            o = run(str(fd), current_phase=4, stage1_status="PASSED",
                    recycle_count=0, recycle_cap=3)
            assert o["outcome"] == "PASS", f"{fd.name}: clean → PASS, got {o['outcome']}"
            assert o["stage2_dirty"] == {}, f"{fd.name}: no spurious dirty"

    def test_missing_feature_dir_degrades_not_crash(self):
        o = run(str(BROKEN / "does-not-exist"), current_phase=3,
                stage1_status="PASSED", recycle_count=0, recycle_cap=3)
        # A missing dir loads as an empty graph (no exception) → not a degraded stage-2,
        # genuinely no nodes to fail → PASS. (The degraded-EXCEPTION path is below.)
        assert o["outcome"] == "PASS"

    def test_degraded_stage2_downgrades_pass_to_contested(self, monkeypatch):
        # F-3 fail-safe fix: if stage-2 (build-graph + reconcile machine-floor) cannot run
        # (load raises), a would-be PASS is downgraded to CONTESTED — never green on an
        # un-run correctness floor (the gate's cardinal sin is a false PASS).
        def _boom(*a, **k):
            raise RuntimeError("graph load failed")
        monkeypatch.setattr(mod, "load_corpus", _boom)
        o = run(str(BROKEN), current_phase=4, stage1_status="PASSED",
                recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "CONTESTED"
        assert o["reason"] == "stage2_degraded_unverified_floor"
        assert o["stage2_degraded"]

    def test_broken_fixture_phase3_recycles_to_design_root(self):
        # From Phase 3 the staleness dirty-set ({gate, task-breakdown}) has no node
        # strictly upstream of phase 3 (task-breakdown OWNS phase 3). Pre-TA.2 this was
        # a flat FAIL. But the BROKEN fixture's REAL root is the phase-2 D-19↔code drift
        # + missing matrix coverage, which `dirty_set` cannot see (D-19/matrix are
        # fresh-by-construction in the loader). The wired reconcile machine-floor catches
        # it → RECYCLE→2 (fix at the design root), the correct RCA outcome, not a FAIL
        # that would send the user to patch phase 3 while the phase-2 drift stays.
        o = run(str(BROKEN), current_phase=3, stage1_status="FAILED",
                recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "RECYCLE"
        assert o["reason"] == "reconcile_invariant_fail_upstream"
        assert o["recycle_target"]["target_phase"] == 2


# --- CLI / crash-safety ---------------------------------------------------

class TestCli:
    def _invoke(self, *args):
        return subprocess.run(
            [sys.executable, str(_SCRIPT), *args],
            capture_output=True, text=True, encoding="utf-8",
        )

    def test_cli_recycle_exit_nonzero(self):
        r = self._invoke("--feature-dir", str(BROKEN), "--phase", "4",
                         "--stage1-status", "FAILED")
        assert r.returncode != 0
        data = json.loads(r.stdout)
        assert data["outcome"] == "RECYCLE"

    def test_cli_clean_pass_exit_zero(self):
        feat = next(p for p in sorted(CLEAN.iterdir()) if p.is_dir())
        r = self._invoke("--feature-dir", str(feat), "--phase", "4",
                         "--stage1-status", "PASSED")
        assert r.returncode == 0
        assert json.loads(r.stdout)["outcome"] == "PASS"

    def test_cli_cap_blocks(self):
        r = self._invoke("--feature-dir", str(BROKEN), "--phase", "4",
                         "--stage1-status", "FAILED",
                         "--recycle-count", "3", "--recycle-cap", "3")
        data = json.loads(r.stdout)
        assert data["outcome"] == "BLOCKED"
        assert data["reason"] == "recycle_cap_exceeded"


# --- TA.8 circuit-breaker -------------------------------------------------

class TestCircuitBreaker:
    def test_cap_hit_surfaces_circuit_breaker_not_silent_blocked(self):
        # Cap hit with dirty upstream → BLOCKED, but now with a circuit_breaker
        # decision surface (re-slice/defer/kill), not a dead-end.
        o = compose_outcome("FAILED", {"D-02": ["x"]}, current_phase=3,
                            recycle_count=3, recycle_cap=3)
        assert o["outcome"] == "BLOCKED"
        assert o["reason"] == "recycle_cap_exceeded"
        cb = o["circuit_breaker"]
        assert cb["triggered"] is True
        assert cb["reason"] == "appetite_blown"
        actions = {opt["action"] for opt in cb["options"]}
        assert actions == {"re-slice", "defer", "kill"}
        assert cb["decision"] == "user"  # gate recommends; user decides
        assert cb["recommended"] in actions

    def test_circuit_breaker_only_on_cap_not_normal_recycle(self):
        # Below cap → RECYCLE, no circuit-breaker (it is not a blown appetite yet).
        o = compose_outcome("FAILED", {"D-02": ["x"]}, current_phase=3,
                            recycle_count=2, recycle_cap=3)
        assert o["outcome"] == "RECYCLE"
        assert "circuit_breaker" not in o

    def test_circuit_breaker_not_on_local_fail(self):
        # No dirty upstream → local FAIL, never a circuit-breaker even at high count.
        o = compose_outcome("FAILED", {}, current_phase=3,
                            recycle_count=9, recycle_cap=3)
        assert o["outcome"] == "FAIL"
        assert "circuit_breaker" not in o

    def test_circuit_breaker_not_on_stage1_crash(self):
        # A stage-1 crash blocks first; it is a crash, not a blown appetite.
        o = compose_outcome("BLOCKED", {"D-02": ["x"]}, current_phase=3,
                            recycle_count=9, recycle_cap=3)
        assert o["outcome"] == "BLOCKED"
        assert o["reason"] == "stage1_blocked"
        assert "circuit_breaker" not in o

    def test_breadth_drives_recommendation(self):
        wide = circuit_breaker({"node": "D-02", "target_phase": 1,
                                "all_dirty_upstream": ["D-02", "matrix"]}, 4, 3, 3)
        narrow = circuit_breaker({"node": "D-02", "target_phase": 1,
                                  "all_dirty_upstream": ["D-02"]}, 4, 3, 3)
        assert wide["recommended"] == "re-slice"   # broad churn → re-slice
        assert narrow["recommended"] == "defer"    # single stuck node → defer

    def test_circuit_breaker_deterministic(self):
        a = circuit_breaker({"node": "D-02", "target_phase": 1,
                             "all_dirty_upstream": ["D-02"]}, 3, 3, 3)
        b = circuit_breaker({"node": "D-02", "target_phase": 1,
                             "all_dirty_upstream": ["D-02"]}, 3, 3, 3)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

    def test_cli_cap_surfaces_circuit_breaker(self):
        r = subprocess.run(
            [sys.executable, str(_SCRIPT), "--feature-dir", str(BROKEN),
             "--phase", "4", "--stage1-status", "FAILED",
             "--recycle-count", "3", "--recycle-cap", "3"],
            capture_output=True, text=True, encoding="utf-8")
        data = json.loads(r.stdout)
        assert data["outcome"] == "BLOCKED"
        assert data["circuit_breaker"]["triggered"] is True


# --- TA.4 tier threading into the outcome ---------------------------------

class TestTierThreading:
    def test_tier_dict_attached_to_output(self):
        tier = {"tier_verdict": "PASSED", "knockout": {"status": "PASSED"},
                "scorecard": {"passed": 3, "total": 4}}
        o = compose_outcome("PASSED", {}, current_phase=2,
                            recycle_count=0, recycle_cap=3, tier=tier)
        assert o["tier"] == tier
        assert o["outcome"] == "PASS"

    def test_tier_none_default_still_reserved(self):
        # No regression to TA.3: default tier is None, field still present.
        o = compose_outcome("PASSED", {}, current_phase=2, recycle_count=0, recycle_cap=3)
        assert o["tier"] is None

    def test_must_knockout_status_drives_outcome_fail(self):
        # The TA.4 knockout (FAILED) fed as stage-1 → local FAIL with no dirty upstream.
        tier = {"tier_verdict": "FAILED", "knockout": {"status": "FAILED",
                "must_failed": ["M1"]}, "scorecard": {"passed": 4, "total": 4}}
        o = compose_outcome(tier["knockout"]["status"], {}, current_phase=2,
                            recycle_count=0, recycle_cap=3, tier=tier)
        assert o["outcome"] == "FAIL"
        # the perfect scorecard does NOT rescue the must-knockout
        assert o["tier"]["scorecard"]["passed"] == 4

    def test_cli_tier_json_drives_stage1(self, tmp_path):
        tier = {"tier_verdict": "FAILED", "knockout": {"status": "FAILED"}}
        tf = tmp_path / "tier.json"
        tf.write_text(json.dumps(tier), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(_SCRIPT), "--feature-dir",
             str(BROKEN / "does-not-exist"), "--phase", "2",
             "--tier-json", str(tf)],
            capture_output=True, text=True, encoding="utf-8")
        data = json.loads(r.stdout)
        # no dirty upstream resolvable + knockout FAILED → local FAIL, tier attached
        assert data["outcome"] == "FAIL"
        assert data["tier"]["knockout"]["status"] == "FAILED"

    def test_cli_requires_stage1_or_tier(self):
        r = subprocess.run(
            [sys.executable, str(_SCRIPT), "--feature-dir", str(BROKEN), "--phase", "2"],
            capture_output=True, text=True, encoding="utf-8")
        assert r.returncode != 0
        assert "stage1-status or --tier-json" in r.stderr


# --- TA.2 reconcile stage-2 helpers ---------------------------------------

class TestReconcileTargets:
    def test_no_report_is_empty_none_safe(self):
        assert reconcile_invariant_targets(None) == []
        assert reconcile_invariant_targets({}) == []

    def test_clean_report_no_targets(self):
        rep = _report(("D-19", False, []), ("matrix", False, []))
        assert reconcile_invariant_targets(rep) == []

    def test_extracts_invariant_fail_with_owning_phase(self):
        rep = _report(("D-19", True, [{"check": "model_drift"}]), ("matrix", False, []))
        targets = reconcile_invariant_targets(rep)
        assert len(targets) == 1
        assert targets[0]["node"] == "D-19"
        assert targets[0]["owning_phase"] == 2
        assert targets[0]["floor_reasons"] == [{"check": "model_drift"}]

    def test_sorted_by_owning_phase_then_node(self):
        rep = _report(("matrix", True, []), ("D-02", True, []), ("D-19", True, []))
        targets = reconcile_invariant_targets(rep)
        # D-02 (phase 1) first, then D-19 then matrix (both phase 2, node id tiebreak)
        assert [t["node"] for t in targets] == ["D-02", "D-19", "matrix"]

    def test_unmapped_node_sorts_last_none_owning(self):
        rep = _report(("mystery", True, []), ("D-02", True, []))
        targets = reconcile_invariant_targets(rep)
        assert targets[0]["node"] == "D-02"
        assert targets[-1]["node"] == "mystery"
        assert targets[-1]["owning_phase"] is None

    def test_select_recycle_picks_earliest_upstream(self):
        targets = reconcile_invariant_targets(
            _report(("matrix", True, []), ("D-02", True, [])))
        rec = select_reconcile_recycle(targets, current_phase=4)
        assert rec["target_phase"] == 1  # D-02 earliest
        assert rec["node"] == "D-02"
        assert rec["k"] == 3

    def test_select_recycle_none_when_local_only(self):
        # D-19 owns phase 2; from phase 2 it is NOT strictly upstream → local FAIL.
        targets = reconcile_invariant_targets(_report(("D-19", True, [])))
        assert select_reconcile_recycle(targets, current_phase=2) is None

    def test_select_recycle_none_when_unmapped_only(self):
        targets = reconcile_invariant_targets(_report(("mystery", True, [])))
        assert select_reconcile_recycle(targets, current_phase=4) is None


# --- TA.2 reconcile knockout composed into the precedence -----------------

class TestReconcileKnockout:
    def test_invariant_fail_blocks_pass_even_stage1_passed(self):
        # THE load-bearing fix: stage-1 PASSED + no staleness + a machine-floor RED
        # whose root is upstream → NEVER PASS; RECYCLE to the root phase.
        rep = _report(("D-19", True, [{"check": "model_drift"}]))
        o = compose_outcome("PASSED", {}, current_phase=4, recycle_count=0,
                            recycle_cap=3, reconcile=rep)
        assert o["outcome"] != "PASS"
        assert o["outcome"] == "RECYCLE"
        assert o["reason"] == "reconcile_invariant_fail_upstream"
        assert o["recycle_target"]["target_phase"] == 2

    def test_reconcile_recycle_honors_loop_cap(self):
        # F-3 fix: the reconcile-invariant RECYCLE path must honor the SAME loop cap as
        # staleness — it is precisely the path staleness misses (D-19 fresh-by-construction),
        # so without this it would recycle forever.
        rep = _report(("D-19", True, [{"check": "model_drift"}]))
        capped = compose_outcome("PASSED", {}, current_phase=4, recycle_count=3,
                                 recycle_cap=3, reconcile=rep)
        assert capped["outcome"] == "BLOCKED"
        assert capped["reason"] == "recycle_cap_exceeded"
        assert "circuit_breaker" in capped
        # below the cap the same case still RECYCLEs
        below = compose_outcome("PASSED", {}, current_phase=4, recycle_count=2,
                                recycle_cap=3, reconcile=rep)
        assert below["outcome"] == "RECYCLE"

    def test_invariant_fail_local_is_fail_not_pass(self):
        # Machine-floor RED local to the current phase (D-19 owns phase 2) → FAIL.
        rep = _report(("D-19", True, [{"check": "model_drift"}]))
        o = compose_outcome("PASSED", {}, current_phase=2, recycle_count=0,
                            recycle_cap=3, reconcile=rep)
        assert o["outcome"] == "FAIL"
        assert o["reason"] == "reconcile_invariant_fail"
        # evidence is surfaced from the verdict's floor_reasons (reused, not re-counted)
        assert o["invariant_fail_nodes"][0]["floor_reasons"] == [{"check": "model_drift"}]

    def test_clean_reconcile_still_passes(self):
        rep = _report(("D-19", False, []), ("matrix", False, []))
        o = compose_outcome("PASSED", {}, current_phase=4, recycle_count=0,
                            recycle_cap=3, reconcile=rep)
        assert o["outcome"] == "PASS"
        assert o["reconcile"]["any_invariant_fail"] is False

    def test_staleness_recycle_takes_precedence_over_reconcile(self):
        # When BOTH a dirty upstream and an invariant-fail exist, staleness RECYCLE
        # fires first (it owns the same earliest-root rule); the invariant is still
        # recorded in the `reconcile` surface so nothing is masked.
        rep = _report(("D-19", True, []))
        o = compose_outcome("PASSED", {"D-02": ["direct"]}, current_phase=4,
                            recycle_count=0, recycle_cap=3, reconcile=rep)
        assert o["outcome"] == "RECYCLE"
        assert o["reason"] == "upstream_dirty"
        assert o["reconcile"]["any_invariant_fail"] is True  # not lost

    def test_crash_dominates_reconcile(self):
        rep = _report(("D-19", True, []))
        o = compose_outcome("BLOCKED", {}, current_phase=4, recycle_count=0,
                            recycle_cap=3, reconcile=rep)
        assert o["outcome"] == "BLOCKED"
        assert o["reason"] == "stage1_blocked"

    def test_loop_cap_dominates_reconcile(self):
        # Cap-hit on a dirty upstream BLOCKS before the reconcile branch.
        rep = _report(("D-19", True, []))
        o = compose_outcome("FAILED", {"D-02": ["x"]}, current_phase=4,
                            recycle_count=3, recycle_cap=3, reconcile=rep)
        assert o["outcome"] == "BLOCKED"
        assert o["reason"] == "recycle_cap_exceeded"

    def test_invariant_not_downgradable_by_failed_stage1(self):
        # Even a FAILED stage-1 with an upstream invariant root recycles to the root
        # (fix upstream), never silently becomes a local FAIL that hides the root.
        rep = _report(("D-02", True, []))
        o = compose_outcome("FAILED", {}, current_phase=3, recycle_count=0,
                            recycle_cap=3, reconcile=rep)
        assert o["outcome"] == "RECYCLE"
        assert o["recycle_target"]["target_phase"] == 1

    def test_reconcile_none_when_degraded_no_knockout(self):
        # reconcile=None (degraded stage-2) → no knockout asserted; stage-1 PASS passes.
        o = compose_outcome("PASSED", {}, current_phase=4, recycle_count=0,
                            recycle_cap=3, reconcile=None)
        assert o["outcome"] == "PASS"
        assert o["reconcile"] is None

    def test_deterministic_with_reconcile(self):
        rep = _report(("D-19", True, [{"check": "model_drift"}]), ("matrix", True, []))
        a = compose_outcome("PASSED", {}, 4, 0, 3, reconcile=rep)
        b = compose_outcome("PASSED", {}, 4, 0, 3, reconcile=rep)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# --- TA.2 the load-bearing eval on the real corpora -----------------------

class TestReconcileEval:
    def test_broken_fixture_stage1_passed_never_passes(self):
        # Force stage-1 = PASSED on the BROKEN fixture. The gate must STILL not PASS:
        # reconcile invariant-fail on D-19↔code drift + missing matrix rows. This is
        # the RCA hole `dirty_set` alone left open.
        o = run(str(BROKEN), current_phase=4, stage1_status="PASSED",
                recycle_count=0, recycle_cap=3)
        assert o["outcome"] != "PASS"
        assert o["reconcile"]["any_invariant_fail"] is True

    def test_broken_fixture_phase2_stage1_passed_fails_on_reconcile(self):
        # At phase 2, D-19/matrix invariant-fail is LOCAL (no staleness upstream of
        # phase 2 here) → FAIL on the reconcile machine-floor, not PASS.
        o = run(str(BROKEN), current_phase=2, stage1_status="PASSED",
                recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "FAIL"
        assert o["reason"] == "reconcile_invariant_fail"
        nodes = {n["node"] for n in o["invariant_fail_nodes"]}
        assert {"D-19", "matrix"} <= nodes

    def test_clean_corpus_stage1_passed_passes(self):
        feats = [p for p in sorted(CLEAN.iterdir()) if p.is_dir()]
        for fd in feats:
            o = run(str(fd), current_phase=4, stage1_status="PASSED",
                    recycle_count=0, recycle_cap=3)
            assert o["outcome"] == "PASS", f"{fd.name}: clean → PASS, got {o['outcome']}"
            assert o["reconcile"]["any_invariant_fail"] is False, f"{fd.name}: no spurious invariant-fail"

    def test_cli_broken_stage1_passed_exit_nonzero(self):
        r = subprocess.run(
            [sys.executable, str(_SCRIPT), "--feature-dir", str(BROKEN),
             "--phase", "2", "--stage1-status", "PASSED"],
            capture_output=True, text=True, encoding="utf-8")
        assert r.returncode != 0
        data = json.loads(r.stdout)
        assert data["outcome"] != "PASS"
        assert data["reconcile"]["any_invariant_fail"] is True
