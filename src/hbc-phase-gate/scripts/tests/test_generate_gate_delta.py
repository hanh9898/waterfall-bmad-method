#!/usr/bin/env python3
"""Tests for generate-gate-delta.py."""

import json
import os

from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "generate_gate_delta",
    os.path.join(os.path.dirname(__file__), "..", "generate-gate-delta.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

load_results = mod.load_results
compute_delta = mod.compute_delta
summarize = mod.summarize
render_markdown = mod.render_markdown
render_json = mod.render_json


def _write_eval(path: str, items: list[dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {"summary": {}, "results": items}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def _make_item(item_id: str, status: str) -> dict:
    return {"item_id": item_id, "status": status, "type": "FILE", "required": True}


class TestLoadResults:
    def test_extracts_id_status_map(self, tmp_path):
        path = str(tmp_path / "eval.json")
        _write_eval(path, [_make_item("P1-01", "PASS"), _make_item("P1-02", "FAIL")])
        result = load_results(path)
        assert result == {"P1-01": "PASS", "P1-02": "FAIL"}

    def test_empty_results(self, tmp_path):
        path = str(tmp_path / "eval.json")
        _write_eval(path, [])
        assert load_results(path) == {}


class TestComputeDelta:
    def test_unchanged_items(self):
        prior = {"P1-01": "PASS", "P1-02": "FAIL"}
        current = {"P1-01": "PASS", "P1-02": "FAIL"}
        rows = compute_delta(prior, current)
        assert all(r["change"] == "—" for r in rows)

    def test_fixed_item(self):
        prior = {"P1-01": "FAIL"}
        current = {"P1-01": "PASS"}
        rows = compute_delta(prior, current)
        assert rows[0]["change"] == "FAIL→PASS"

    def test_regressed_item(self):
        prior = {"P1-01": "PASS"}
        current = {"P1-01": "FAIL"}
        rows = compute_delta(prior, current)
        assert rows[0]["change"] == "PASS→FAIL"

    def test_new_item(self):
        prior = {"P1-01": "PASS"}
        current = {"P1-01": "PASS", "P1-02": "FAIL"}
        rows = compute_delta(prior, current)
        new_row = next(r for r in rows if r["item_id"] == "P1-02")
        assert new_row["change"] == "NEW"

    def test_removed_item(self):
        prior = {"P1-01": "PASS", "P1-02": "FAIL"}
        current = {"P1-01": "PASS"}
        rows = compute_delta(prior, current)
        removed = next(r for r in rows if r["item_id"] == "P1-02")
        assert removed["current"] == "—"

    def test_preserves_order(self):
        prior = {"P1-01": "PASS", "P1-02": "FAIL", "P1-03": "PASS"}
        current = {"P1-01": "PASS", "P1-02": "PASS", "P1-03": "PASS"}
        rows = compute_delta(prior, current)
        assert [r["item_id"] for r in rows] == ["P1-01", "P1-02", "P1-03"]


class TestSummarize:
    def test_mixed_changes(self):
        rows = [
            {"item_id": "P1-01", "previous": "FAIL", "current": "PASS", "change": "FAIL→PASS"},
            {"item_id": "P1-02", "previous": "PASS", "current": "FAIL", "change": "PASS→FAIL"},
            {"item_id": "P1-03", "previous": "PASS", "current": "PASS", "change": "—"},
            {"item_id": "P1-04", "previous": "—", "current": "PASS", "change": "NEW"},
        ]
        s = summarize(rows)
        assert s == {"fixed": 1, "regressed": 1, "new": 1, "unchanged": 1}

    def test_empty_rows(self):
        s = summarize([])
        assert s == {"fixed": 0, "regressed": 0, "new": 0, "unchanged": 0}


class TestRenderMarkdown:
    def test_contains_table_header(self):
        rows = [{"item_id": "P1-01", "previous": "FAIL", "current": "PASS", "change": "FAIL→PASS"}]
        summary = {"fixed": 1, "regressed": 0, "new": 0, "unchanged": 0}
        md = render_markdown(rows, summary, "PASSED")
        assert "| Item ID | Previous | Current | Change |" in md
        assert "PASSED" in md
        assert "1 fixed" in md

    def test_contains_item_row(self):
        rows = [{"item_id": "P2-03", "previous": "PASS", "current": "FAIL", "change": "PASS→FAIL"}]
        summary = {"fixed": 0, "regressed": 1, "new": 0, "unchanged": 0}
        md = render_markdown(rows, summary, "FAILED")
        assert "P2-03" in md
        assert "PASS→FAIL" in md


class TestRenderJson:
    def test_categorizes_items(self):
        rows = [
            {"item_id": "P1-01", "previous": "FAIL", "current": "PASS", "change": "FAIL→PASS"},
            {"item_id": "P1-02", "previous": "PASS", "current": "FAIL", "change": "PASS→FAIL"},
            {"item_id": "P1-03", "previous": "—", "current": "PASS", "change": "NEW"},
            {"item_id": "P1-04", "previous": "PASS", "current": "PASS", "change": "—"},
        ]
        summary = {"fixed": 1, "regressed": 1, "new": 1, "unchanged": 1}
        result = render_json(rows, summary)
        assert result["fixed"] == ["P1-01"]
        assert result["regressed"] == ["P1-02"]
        assert result["new"] == ["P1-03"]
        assert result["unchanged"] == ["P1-04"]


class TestCLI:
    def test_first_run_no_prior(self, tmp_path):
        import subprocess, sys

        current_path = str(tmp_path / "current.json")
        out_path = str(tmp_path / "delta.md")
        _write_eval(current_path, [_make_item("P1-01", "PASS")])

        script = os.path.join(os.path.dirname(__file__), "..", "generate-gate-delta.py")
        result = subprocess.run(
            [sys.executable, script, current_path, "--status", "PASSED", "-o", out_path],
            capture_output=True,
        )
        assert result.returncode == 0
        content = open(out_path, encoding="utf-8").read()
        assert "First evaluation" in content

    def test_with_prior_no_regressions(self, tmp_path):
        import subprocess, sys

        prior_path = str(tmp_path / "prior.json")
        current_path = str(tmp_path / "current.json")
        out_path = str(tmp_path / "delta.md")
        _write_eval(prior_path, [_make_item("P1-01", "FAIL")])
        _write_eval(current_path, [_make_item("P1-01", "PASS")])

        script = os.path.join(os.path.dirname(__file__), "..", "generate-gate-delta.py")
        result = subprocess.run(
            [sys.executable, script, current_path, "--prior", prior_path, "--status", "PASSED", "-o", out_path],
            capture_output=True,
        )
        assert result.returncode == 0
        content = open(out_path, encoding="utf-8").read()
        assert "FAIL→PASS" in content

    def test_exit_code_1_on_regression(self, tmp_path):
        import subprocess, sys

        prior_path = str(tmp_path / "prior.json")
        current_path = str(tmp_path / "current.json")
        _write_eval(prior_path, [_make_item("P1-01", "PASS")])
        _write_eval(current_path, [_make_item("P1-01", "FAIL")])

        script = os.path.join(os.path.dirname(__file__), "..", "generate-gate-delta.py")
        result = subprocess.run(
            [sys.executable, script, current_path, "--prior", prior_path, "--status", "FAILED"],
            capture_output=True,
        )
        assert result.returncode == 1
