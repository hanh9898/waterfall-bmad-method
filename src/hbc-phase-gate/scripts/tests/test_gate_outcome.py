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
run = mod.run
DEFAULT_RECYCLE_CAP = mod.DEFAULT_RECYCLE_CAP


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
        # No upstream resolvable → empty dirty-set; stage-1 PASS → PASS (degraded note).
        assert o["outcome"] == "PASS"

    def test_broken_fixture_phase3_taskbreakdown_not_upstream(self):
        # From Phase 3, task-breakdown (owns phase 3) is NOT strictly upstream, so
        # it does not trigger a recycle; with stage-1 FAILED it's a local FAIL.
        o = run(str(BROKEN), current_phase=3, stage1_status="FAILED",
                recycle_count=0, recycle_cap=3)
        assert o["outcome"] == "FAIL"


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
