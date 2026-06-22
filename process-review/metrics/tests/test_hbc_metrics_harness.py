"""Tests for the HBC F-6 metrics harness (TF.3).

Run from repo root:  python -m pytest process-review/metrics/tests
Invokes the harness the way the runbook does (subprocess + JSON stdout) and also
unit-tests the pure metric functions against the frozen TD.0 fixture baselines.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parents[1] / "hbc_metrics_harness.py"
FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "resource-plan-billable"
INTEGRITY = Path(__file__).resolve().parents[2] / "fixtures" / "fixture_integrity.py"

sys.path.insert(0, str(HARNESS.parent))
import hbc_metrics_harness as h  # noqa: E402


# --- the frozen baseline contract (TD.0). If these drift, the fixture changed. ---
EXPECTED = {
    "d02_churn": 13,
    "spec_ref_leak": 44,
    "req_without_matrix_row": 3,
    "gate_false_pass": 2,  # structural (failed/override); 1 further stale-pass not counted
    "model_drift": 5,
    "recascade": None,  # non-mechanical
}


def test_fixture_exists():
    assert FIXTURE.is_dir(), "TD.0 fixture missing"
    assert (FIXTURE / "FIXTURE.md").is_file()
    assert (FIXTURE / "artifacts").is_dir()
    assert (FIXTURE / "code").is_dir()


def test_run_returns_all_metrics():
    report = h.run(FIXTURE)
    ids = {m["id"] for m in report["metrics"]}
    assert ids == set(EXPECTED)
    assert report["mechanical_count"] == 5


@pytest.mark.parametrize("metric_id,expected", EXPECTED.items())
def test_baselines(metric_id, expected):
    report = h.run(FIXTURE)
    m = next(x for x in report["metrics"] if x["id"] == metric_id)
    assert m["baseline_measured"] == expected


def test_spec_ref_breakdown_prod_matches_rca():
    report = h.run(FIXTURE)
    m = next(x for x in report["metrics"] if x["id"] == "spec_ref_leak")
    # prod portion must match the RCA exactly — proves the counting method is sound
    assert m["baseline_breakdown"]["prod"] == 29


def test_missing_reqs_are_040_041_042():
    report = h.run(FIXTURE)
    m = next(x for x in report["metrics"] if x["id"] == "req_without_matrix_row")
    nums = sorted(int(s.split("-")[-1]) for s in m["missing"])
    assert nums == [40, 41, 42]


def test_model_drift_tokens_absent_from_code():
    report = h.run(FIXTURE)
    m = next(x for x in report["metrics"] if x["id"] == "model_drift")
    # every drift token is in design but not in code
    for row in m["token_matrix"]:
        if row["token"] in m["drift_tokens"]:
            assert row["in_design"] and not row["in_code"]


def test_recascade_is_honest_non_mechanical():
    report = h.run(FIXTURE)
    m = next(x for x in report["metrics"] if x["id"] == "recascade")
    assert m["mechanical"] is False
    assert m["baseline_measured"] is None
    assert m["documented_baseline"] == 4


def test_cli_emits_valid_json():
    proc = subprocess.run(
        [sys.executable, str(HARNESS)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["metric_count"] == 6


def test_cli_missing_fixture_errors_nonzero(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--fixture", str(tmp_path / "nope")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 1
    assert "error" in proc.stderr.lower()


def test_gate_false_pass_is_structural():
    """The counted gates carry an at-gate-time signal; stale-only passes are not counted."""
    report = h.run(FIXTURE)
    m = next(x for x in report["metrics"] if x["id"] == "gate_false_pass")
    for g in m["false_pass_gates"]:
        assert g["failed"] > 0 or g["manual_override"]
    # at least one further PASSED gate is a stale-pass we deliberately do not count
    assert len(m["stale_pass_context"]) >= 1


def test_is_pass_rejects_lookalikes():
    """BYPASSED / NOT PASSED / PASSED-with-suffix must not count as a clean pass."""
    assert h._is_pass("PASSED") and h._is_pass("pass")
    for bad in ("BYPASSED", "NOT PASSED", "PASSED (manual)", "COMPASS", None):
        assert not h._is_pass(bad)


def test_token_in_respects_word_boundary():
    """A design token must not match as a substring of a longer identifier."""
    assert not h._token_in("request_line", "purchase_request_lines = []")
    assert h._token_in("request_line", "self.request_line = x")
    # dotted Odoo model name matches as a literal
    assert h._token_in("resource.plan.request", "_name = 'resource.plan.request'")


def test_fixture_integrity_check_passes():
    """The committed manifest must match the fixture bytes exactly (H1/H2 tamper-evidence)."""
    proc = subprocess.run(
        [sys.executable, str(INTEGRITY), "--check"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_recascade_fallback_when_no_logs(tmp_path):
    """No runtime cascade-log → non-mechanical fallback with documented baseline (CLN-1)."""
    m = h.metric_recascade(tmp_path)
    assert m["mechanical"] is False
    assert m["baseline_measured"] is None
    assert m["documented_baseline"] == 4


def test_recascade_mechanical_when_logs_present(tmp_path):
    """With .cascade-log.jsonl present, re-cascade is measured = worst-feature round count (CLN-1)."""
    tr = tmp_path / "features" / "auth" / "traceability"
    tr.mkdir(parents=True)
    (tr / ".cascade-log.jsonl").write_text('{"round": 1}\n{"round": 2}\n', encoding="utf-8")
    tr2 = tmp_path / "features" / "billing" / "traceability"
    tr2.mkdir(parents=True)
    (tr2 / ".cascade-log.jsonl").write_text('{"round": 1}\n', encoding="utf-8")
    m = h.metric_recascade(tmp_path)
    assert m["mechanical"] is True
    assert m["baseline_measured"] == 2  # worst feature (auth)
    assert m["per_feature"] == {"auth": 2, "billing": 1}
