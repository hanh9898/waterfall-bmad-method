#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for build-graph.py (TA.1 wiring). Run via pytest or `python test_build_graph.py`.

Calls the script the way SKILL.md does (subprocess), and asserts the living-graph
proof end-to-end: broken fixture → non-empty dirty-set + missing edges + drift;
clean corpus → empty dirty-set / no missing edges / no drift.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "build-graph.py"
_REPO = Path(__file__).resolve().parents[4]  # tests → scripts → hbc-traceability → src → repo
BROKEN = _REPO / "process-review" / "fixtures" / "resource-plan-billable"
CLEAN = _REPO / "process-review" / "spikes" / "ta0" / "corpus-clean"


def run(*args, expect_code=None):
    p = subprocess.run([sys.executable, str(SCRIPT), *args],
                       capture_output=True, text=True, encoding="utf-8")
    if expect_code is not None:
        assert p.returncode == expect_code, f"exit {p.returncode} != {expect_code}\n{p.stdout}\n{p.stderr}"
    data = json.loads(p.stdout) if p.stdout.strip() else {"_stderr": p.stderr}
    return data, p.returncode


def test_missing_feature_dir_io_error():
    _data, code = run("--feature-dir", str(_REPO / "no-such-dir"), expect_code=2)
    assert code == 2


def test_broken_fixture_dirty_and_missing_edges():
    data, code = run("--feature-dir", str(BROKEN), expect_code=0)
    assert data["dirty_set"], "broken fixture: dirty-set must be non-empty"
    assert "gate" in data["dirty_set"] and "task-breakdown" in data["dirty_set"]
    me = set(data["missing_edges"])
    assert any("040" in r for r in me) and any("041" in r for r in me) and any("042" in r for r in me)


def test_broken_fixture_ground_truth_drift():
    data, _ = run("--feature-dir", str(BROKEN), expect_code=0)
    drift = data["ground_truth_drift"]
    assert drift and any(d["drift"] for d in drift)


def test_broken_fixture_matrix_view_shape():
    data, _ = run("--feature-dir", str(BROKEN), expect_code=0)
    view = data["matrix_view"]
    assert view["source_doc"] == "D-02"
    assert view["matrix_node"] == "matrix"
    assert isinstance(view["reqs"], list) and view["reqs"]


def test_clean_corpus_empty_signal():
    for feat in ("resource-plan-billable", "project-tag-filter"):
        data, code = run("--feature-dir", str(CLEAN / feat), expect_code=0)
        assert data["dirty_set"] == {}, f"{feat}: dirty-set must be empty"
        assert data["missing_edges"] == [], f"{feat}: no missing edges"
        assert all(not d["drift"] for d in data["ground_truth_drift"]), f"{feat}: no false drift"


def test_deterministic_across_runs():
    a, _ = run("--feature-dir", str(BROKEN), expect_code=0)
    b, _ = run("--feature-dir", str(BROKEN), expect_code=0)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
