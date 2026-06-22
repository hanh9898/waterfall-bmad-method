#!/usr/bin/env python
"""Smoke-test for the TA.0 spike (throwaway). Asserts the GO-bar outcome so the
result is re-checkable: broken catches the 4 known errors with graph evidence,
clean produces 0 false-positives on a non-empty multi-feature corpus.

Run:  python process-review/spikes/ta0/test_spike.py
(or  python -m pytest process-review/spikes/ta0/test_spike.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "kernel"))

from buildgraph import run_graph  # noqa: E402
from loader import load_corpus    # noqa: E402

REPO_ROOT = HERE.parents[2]
BROKEN = REPO_ROOT / "process-review" / "fixtures" / "resource-plan-billable"

EXPECTED = {"gate-STALE", "matrix-missing-reqs", "model-drift", "taskbreakdown-missing-slices"}


def test_broken_catches_all_4():
    g = load_corpus(BROKEN)
    caught = {c["error"] for c in run_graph(g)["caught"]}
    assert EXPECTED.issubset(caught), f"missing: {EXPECTED - caught}"


def test_broken_gate_stale_from_graph():
    g = load_corpus(BROKEN)
    dirty = g.dirty_set()
    assert "gate" in dirty, "gate node should be in the dirty-set"
    assert "task-breakdown" in dirty


def test_broken_model_drift_lists_request_model():
    g = load_corpus(BROKEN)
    md = next(c for c in run_graph(g)["caught"] if c["error"] == "model-drift")
    assert "resource.plan.request" in md["design_only"]


def test_broken_matrix_missing_040_041_042():
    g = load_corpus(BROKEN)
    mm = next(c for c in run_graph(g)["caught"] if c["error"] == "matrix-missing-reqs")
    nums = {int(r.split("-")[-1]) for r in mm["missing_edges"]}
    assert {40, 41, 42}.issubset(nums)


def test_clean_features_have_zero_false_positives():
    for feat in ("resource-plan-billable", "project-tag-filter"):
        g = load_corpus(HERE / "corpus-clean" / feat)
        # all 6 nodes present → no detector is skipped vacuously
        assert {"D-02", "D-19", "code", "matrix", "task-breakdown", "gate"}.issubset(set(g.nodes))
        caught = run_graph(g)["caught"]
        assert caught == [], f"{feat} false-positive: {caught}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\nALL {len(fns)} spike tests passed.")
