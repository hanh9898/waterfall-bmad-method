#!/usr/bin/env python3
"""Tests for gate-tier.py — TA.4 tier-aware verdict (must-knockout / should-scorecard)."""

import json
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_HERE = Path(__file__).resolve()
_SCRIPT = _HERE.parents[1] / "gate-tier.py"

_spec = spec_from_file_location("gate_tier", str(_SCRIPT))
assert _spec is not None and _spec.loader is not None
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

tier_verdict = mod.tier_verdict
_is_must = mod._is_must
run = mod.run
DEFAULT_SHOULD_FLOOR = mod.DEFAULT_SHOULD_FLOOR


def _item(item_id, status, *, required=False, type="QUALITY",
          criteria="", description="", pattern=""):
    return {"item_id": item_id, "status": status, "required": required,
            "type": type, "criteria": criteria, "description": description,
            "artifact_pattern": pattern}


# --- _is_must tiering ------------------------------------------------------

class TestTiering:
    def test_required_item_is_must(self):
        assert _is_must(_item("R", "PASS", required=True)) is True

    def test_non_required_is_should(self):
        assert _is_must(_item("S", "PASS", required=False)) is False

    def test_matrix_required_is_must(self):
        assert _is_must(_item("M", "PASS", required=True, type="MATRIX")) is True

    def test_entry_gate_is_must(self):
        it = _item("E", "PASS", required=True, type="CONTENT",
                   pattern="{out}/features/f/gates/phase-1-gate*")
        assert _is_must(it) is True

    def test_correctness_tagged_required_is_must(self):
        it = _item("C", "PASS", required=True, criteria="MODEL_DRIFT clean [correctness]")
        assert _is_must(it) is True

    def test_non_required_correctness_tag_not_pulled_into_must_unless_required(self):
        # The tag rule mirrors the evaluator: it only fires on required items.
        # A non-required tagged item is SHOULD (it is also not `required`).
        assert _is_must(_item("X", "PASS", required=False,
                              criteria="[correctness]")) is False


# --- tier_verdict ----------------------------------------------------------

class TestTierVerdict:
    def test_must_fail_knocks_out_even_with_perfect_scorecard(self):
        results = [
            _item("M1", "FAIL", required=True),
            _item("S1", "PASS"), _item("S2", "PASS"),
        ]
        v = tier_verdict(results)
        assert v["tier_verdict"] == "FAILED"
        assert v["knockout"]["status"] == "FAILED"
        assert "M1" in v["knockout"]["must_failed"]
        # scorecard still reported, perfect
        assert v["scorecard"]["passed"] == 2 and v["scorecard"]["total"] == 2

    def test_should_fail_never_knocks_out(self):
        results = [
            _item("M1", "PASS", required=True),
            _item("S1", "FAIL"), _item("S2", "PASS"),
        ]
        v = tier_verdict(results, gate_mode="strict")
        # clean must-haves → PASSED in strict, scorecard reports the should-fail.
        assert v["tier_verdict"] == "PASSED"
        assert v["knockout"]["status"] == "PASSED"
        assert v["scorecard"] == {"passed": 1, "total": 2, "ratio": 0.5,
                                  "floor": DEFAULT_SHOULD_FLOOR, "below_floor": True,
                                  "not_scored": []}

    def test_lenient_warns_below_floor_but_does_not_block(self):
        results = [
            _item("M1", "PASS", required=True),
            _item("S1", "FAIL"), _item("S2", "PASS"),
        ]
        v = tier_verdict(results, gate_mode="lenient")
        assert v["tier_verdict"] == "WARNING"
        assert v["reason"] == "should_scorecard_below_floor"
        assert v["knockout"]["status"] == "PASSED"  # never a knockout

    def test_lenient_above_floor_passes(self):
        results = [_item("M1", "PASS", required=True)] + \
                  [_item(f"S{i}", "PASS") for i in range(9)] + [_item("Sx", "FAIL")]
        v = tier_verdict(results, gate_mode="lenient")  # 9/10 = 0.9 >= 0.8
        assert v["tier_verdict"] == "PASSED"

    def test_must_contested_is_knockout_not_pass(self):
        results = [_item("M1", "CONTESTED", required=True), _item("S1", "PASS")]
        v = tier_verdict(results)
        assert v["tier_verdict"] == "CONTESTED"
        assert "M1" in v["knockout"]["must_contested"]

    def test_must_blocked_dominates(self):
        results = [_item("M1", "BLOCKED", required=True), _item("M2", "FAIL", required=True)]
        v = tier_verdict(results)
        assert v["tier_verdict"] == "BLOCKED"

    def test_all_clean_passes(self):
        results = [_item("M1", "PASS", required=True), _item("S1", "PASS")]
        v = tier_verdict(results)
        assert v["tier_verdict"] == "PASSED"
        assert v["reason"] == "must_clean"

    def test_pending_and_na_excluded_from_scorecard_denominator(self):
        results = [
            _item("M1", "PASS", required=True),
            _item("S1", "PASS"), _item("S2", "PENDING_LLM"), _item("S3", "NA"),
        ]
        v = tier_verdict(results)
        assert v["scorecard"]["total"] == 1  # only S1 is scored
        assert v["scorecard"]["passed"] == 1
        assert "S2" in v["scorecard"]["not_scored"] and "S3" in v["scorecard"]["not_scored"]

    def test_no_should_items_full_ratio(self):
        results = [_item("M1", "PASS", required=True)]
        v = tier_verdict(results)
        assert v["scorecard"]["ratio"] == 1.0 and v["tier_verdict"] == "PASSED"

    def test_deterministic(self):
        results = [_item("M1", "FAIL", required=True), _item("S1", "FAIL")]
        a = tier_verdict(results)
        b = tier_verdict(results)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# --- run() over evaluator JSON --------------------------------------------

class TestRun:
    def _write(self, tmp_path, payload):
        f = tmp_path / "eval.json"
        f.write_text(json.dumps(payload), encoding="utf-8")
        return str(f)

    def test_reads_gate_mode_from_summary(self, tmp_path):
        payload = {"summary": {"gate_mode": "lenient"},
                   "results": [_item("M1", "PASS", required=True),
                               _item("S1", "FAIL"), _item("S2", "PASS")]}
        v = run(self._write(tmp_path, payload))
        assert v["tier_verdict"] == "WARNING"  # lenient + below floor

    def test_evaluator_blocked_propagates(self, tmp_path):
        payload = {"status": "BLOCKED", "reason": "evaluator_crashed",
                   "summary": {"overall_status": "BLOCKED"}}
        v = run(self._write(tmp_path, payload))
        assert v["tier_verdict"] == "BLOCKED"
        assert v["reason"] == "evaluator_blocked"

    def test_gate_mode_override(self, tmp_path):
        payload = {"summary": {"gate_mode": "strict"},
                   "results": [_item("M1", "PASS", required=True), _item("S1", "FAIL")]}
        v = run(self._write(tmp_path, payload), gate_mode="lenient")
        assert v["tier_verdict"] == "WARNING"


# --- CLI -------------------------------------------------------------------

class TestCli:
    def _invoke(self, *args):
        return subprocess.run([sys.executable, str(_SCRIPT), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def test_cli_knockout_exit_nonzero(self, tmp_path):
        f = tmp_path / "e.json"
        f.write_text(json.dumps({"summary": {"gate_mode": "strict"},
                                 "results": [_item("M1", "FAIL", required=True)]}),
                     encoding="utf-8")
        r = self._invoke(str(f))
        assert r.returncode != 0
        assert json.loads(r.stdout)["tier_verdict"] == "FAILED"

    def test_cli_clean_pass_exit_zero(self, tmp_path):
        f = tmp_path / "e.json"
        f.write_text(json.dumps({"summary": {"gate_mode": "strict"},
                                 "results": [_item("M1", "PASS", required=True)]}),
                     encoding="utf-8")
        r = self._invoke(str(f))
        assert r.returncode == 0
        assert json.loads(r.stdout)["tier_verdict"] == "PASSED"
