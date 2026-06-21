#!/usr/bin/env python3
"""Tests for acceptance-guards.py — the anti-false-ACCEPT engine (B16-1/B16-2/B16-3),
incl. the cardinal proof: the TD.0 broken fixture must NOT be ACCEPT-allowed even
at 100% coverage."""

import json
import os
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "acceptance-guards.py")
_spec = spec_from_file_location("acceptance_guards", _SCRIPT)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

guards = mod.guards

_FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "process-review" / "fixtures" / "resource-plan-billable"
)

_D02 = """---
version: "2.0"
---
# D-02

## Functional Requirements

| ID | Name |
|----|------|
| REQ-001 | a |
| REQ-002 | b |
"""

_MATRIX_COMPLETE = """\
# Matrix

| req_id | design_ref | code_ref | test_ref |
|---|---|---|---|
| REQ-001 | d | c | t |
| REQ-002 | d | c | t |
"""

_MATRIX_MISSING = """\
# Matrix

| req_id | design_ref | code_ref | test_ref |
|---|---|---|---|
| REQ-001 | d | c | t |
"""

_D19 = """# D-19
- **Tên vật lý (Physical name)**: `widget.model`
"""
_CODE_MATCH = "class W(models.Model):\n    _name = 'widget.model'\n"
_CODE_DRIFT = "class W(models.Model):\n    _name = 'old.model'\n"


class TestModelMatch:
    def test_drift_blocks_accept(self):
        res = guards(d19_text=_D19, code_text=_CODE_DRIFT)
        assert res["accept_blocked"] is True
        assert "model_drift" in res["blocking"]
        assert res["accept_allowed"] is False

    def test_match_allows(self):
        res = guards(d19_text=_D19, code_text=_CODE_MATCH)
        assert res["accept_allowed"] is True
        assert res["blocking"] == []


class TestMatrixCompleteness:
    def test_missing_req_blocks(self):
        res = guards(d02_text=_D02, matrix_text=_MATRIX_MISSING)
        assert "missing_from_matrix" in res["blocking"]
        assert res["accept_allowed"] is False

    def test_complete_clean(self):
        res = guards(d02_text=_D02, matrix_text=_MATRIX_COMPLETE)
        assert "missing_from_matrix" not in res["blocking"]


class TestStaleCitation:
    def test_stale_d27_blocks(self):
        d27 = "# D-27\nPer D-02 (v1.0).\n"
        res = guards(d02_text=_D02, d27_text=d27)
        assert "stale_citations" in res["blocking"]
        assert res["accept_allowed"] is False


class TestCoverageNotSufficient:
    def test_high_coverage_does_not_clear_a_block(self):
        # 100% coverage must NOT make a drifted feature accept-allowed (B16-2).
        res = guards(d19_text=_D19, code_text=_CODE_DRIFT, coverage_pct=100.0, coverage_threshold=80.0)
        assert res["coverage"]["meets_threshold"] is True
        assert res["accept_allowed"] is False
        assert res["accept_blocked"] is True

    def test_nothing_checked_not_allowed(self):
        res = guards()
        assert res["accept_allowed"] is False
        assert "note" in res


@pytest.mark.skipif(not _FIXTURE.exists(), reason="TD.0 fixture not present")
class TestTD0NoFalseAccept:
    """THE key proof: the broken RCA case is NEVER accept-allowed, even at 100%."""

    def test_cli_blocks_accept(self):
        pa = _FIXTURE / "artifacts" / "planning-artifacts"
        result = subprocess.run(
            [
                sys.executable, _SCRIPT,
                "--d02", str(pa / "D-02-resource-plan-billable.md"),
                "--d19", str(pa / "D-19-opms" / "D-19-er-diagram.md"),
                "--code-dir", str(_FIXTURE / "code"),
                "--matrix", str(_FIXTURE / "artifacts" / "traceability" / "matrix.md"),
                "--d27", str(pa / "D-27-resource-plan-billable-test-spec.md"),
                "--coverage", "100", "--threshold", "80",
            ],
            capture_output=True, text=True, encoding="utf-8",
        )
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert data["accept_allowed"] is False
        assert data["accept_blocked"] is True
        # all three structural false-ACCEPT signatures fire
        assert "model_drift" in data["blocking"]
        assert "missing_from_matrix" in data["blocking"]
        assert "stale_citations" in data["blocking"]
        # coverage is green yet does NOT license accept
        assert data["coverage"]["meets_threshold"] is True
