#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Tests for check-vpair.py (TA.6 — v_pair design<->test edge enforcement).

Calls the script the way SKILL.md does (subprocess) on the real corpora, plus
synthetic feature dirs for the high-severity (no test edge / no matrix) and
absent-deliverable (no false MISSING) paths. Run via pytest or directly.
"""
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check-vpair.py"
_REPO = Path(__file__).resolve().parents[4]  # tests -> scripts -> hbc-traceability -> src -> repo
BROKEN = _REPO / "process-review" / "fixtures" / "resource-plan-billable"
CLEAN = _REPO / "process-review" / "spikes" / "ta0" / "corpus-clean"


def run(*args, expect_code=None):
    p = subprocess.run([sys.executable, str(SCRIPT), *args],
                       capture_output=True, text=True, encoding="utf-8")
    if expect_code is not None:
        assert p.returncode == expect_code, f"exit {p.returncode} != {expect_code}\n{p.stdout}\n{p.stderr}"
    data = json.loads(p.stdout) if p.stdout.strip() else {"_stderr": p.stderr}
    return data, p.returncode


# --- io / wiring -----------------------------------------------------------
def test_missing_feature_dir_io_error():
    _data, code = run("--feature-dir", str(_REPO / "no-such-dir"), expect_code=2)
    assert code == 2


# --- catalog-driven v_pair map --------------------------------------------
def test_catalog_vpair_map_loaded():
    sys.path.insert(0, str(SCRIPT.parent))
    import importlib.util
    spec = importlib.util.spec_from_file_location("check_vpair", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    vp = mod.load_vpair_map(mod._CATALOG)
    # catalog declares these v_pair levels; null-v_pair deliverables omitted.
    assert vp.get("D-02") == "acceptance"
    assert vp.get("D-19") == "integration-test"
    assert vp.get("D-16") == "unit-test"
    assert vp.get("D-14") == "e2e-test"
    assert "D-03" not in vp and "D-12" not in vp and "D-26" not in vp  # v_pair: null


# --- broken fixture: missing v_pair edges with severity --------------------
def test_broken_fixture_missing_vpair_edges():
    data, code = run("--feature-dir", str(BROKEN), expect_code=1)
    assert data["summary"]["missing"] >= 1
    gaps = {g["deliverable"]: g for g in data["vpair_gaps"]}
    # D-19 is present and declares integration-test; 040/041/042 are not traced.
    assert gaps["D-19"]["status"] == "MISSING"
    assert gaps["D-19"]["expected_test_level"] == "integration-test"
    assert gaps["D-19"]["severity"] in ("high", "medium")
    uncovered = set(gaps["D-19"].get("uncovered_reqs", []))
    assert any("040" in r for r in uncovered)
    assert any("041" in r for r in uncovered)
    assert any("042" in r for r in uncovered)


def test_broken_fixture_present_set_excludes_absent():
    data, _ = run("--feature-dir", str(BROKEN), expect_code=1)
    present = set(data["present_design_deliverables"])
    # D-09/D-14/D-16/D-21 are absent in the fixture -> never flagged.
    assert "D-09" not in present and "D-14" not in present
    assert "D-16" not in present and "D-21" not in present
    flagged = {g["deliverable"] for g in data["vpair_gaps"]}
    assert flagged <= present


# --- clean corpus: no v_pair gaps, absent deliverables not flagged ---------
def test_clean_corpus_no_vpair_gaps():
    for feat in ("resource-plan-billable", "project-tag-filter"):
        data, code = run("--feature-dir", str(CLEAN / feat), expect_code=0)
        assert data["summary"]["missing"] == 0, f"{feat}: no v_pair gaps expected"
        assert all(g["status"] == "present" for g in data["vpair_gaps"]), feat
        present = set(data["present_design_deliverables"])
        # only D-02 + D-19 exist in the clean corpus; nothing else flagged.
        assert present == {"D-02", "D-19"}, f"{feat}: {present}"


# --- high severity: present design but NO test edge / no matrix ------------
def _make_feature(tmp_path, *, with_matrix_test: bool, with_matrix: bool = True):
    feat = tmp_path / "synthetic"
    plan = feat / "planning"
    plan.mkdir(parents=True)
    (plan / "D-02-synthetic.md").write_text(
        "---\nversion: '1.0'\n---\n# Reqs\nREQ-SYN-001 a\nREQ-SYN-002 b\n", encoding="utf-8")
    (plan / "D-19-er-diagram.md").write_text(
        "---\nversion: '1.0'\n---\n# ER\nmodel syn.thing\n", encoding="utf-8")
    if with_matrix:
        tr = feat / "traceability"
        tr.mkdir()
        test_cell = "TC-001" if with_matrix_test else ""
        rows = "\n".join(
            f"| synthetic | REQ-SYN-{n:03d} |  | syn.thing | models/x.py | {test_cell} | PASS | d |"
            for n in (1, 2))
        (tr / "matrix.md").write_text(
            "# Matrix\n\n| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--|--|--|--|--|--|--|--|\n" + rows + "\n", encoding="utf-8")
    return feat


def test_high_severity_no_test_edges(tmp_path):
    feat = _make_feature(tmp_path, with_matrix_test=False)
    data, code = run("--feature-dir", str(feat), expect_code=1)
    gaps = {g["deliverable"]: g for g in data["vpair_gaps"]}
    assert gaps["D-19"]["status"] == "MISSING"
    assert gaps["D-19"]["severity"] == "high"  # matrix has zero test edges
    assert data["summary"]["high"] >= 1


def test_high_severity_no_matrix(tmp_path):
    feat = _make_feature(tmp_path, with_matrix_test=False, with_matrix=False)
    data, code = run("--feature-dir", str(feat), expect_code=1)
    gaps = {g["deliverable"]: g for g in data["vpair_gaps"]}
    assert gaps["D-19"]["severity"] == "high"
    assert "no matrix" in gaps["D-19"]["detail"]


def test_full_coverage_no_gap(tmp_path):
    feat = _make_feature(tmp_path, with_matrix_test=True)
    data, code = run("--feature-dir", str(feat), expect_code=0)
    assert data["summary"]["missing"] == 0


# --- determinism -----------------------------------------------------------
def test_deterministic_across_runs():
    a, _ = run("--feature-dir", str(BROKEN), expect_code=1)
    b, _ = run("--feature-dir", str(BROKEN), expect_code=1)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-q"]))
