#!/usr/bin/env python3
"""Tests for verify-refs.py (B16-1 ref existence + completeness + model-drift,
B16-3 stale-citation), incl. the TD.0 regression fixture (the broken case)."""

import json
import os
import subprocess
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "verify-refs.py")
_spec = spec_from_file_location("verify_refs", _SCRIPT)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

verify = mod.verify
check_matrix_refs = mod.check_matrix_refs

# Repo-root-relative path to the frozen TD.0 fixture (the broken RCA snapshot).
_FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "process-review" / "fixtures" / "resource-plan-billable"
)


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


_MATRIX = """\
# Matrix

| feature | req_id | design_ref | code_ref | test_ref | gate_status |
|---|---|---|---|---|---|
| f | REQ-001 | x | models/a.py | tests/test_a.py |  |
| f | REQ-002 | y | models/missing.py | tests/test_b.py |  |
"""

_D02 = """---
version: "2.0"
---
# D-02

## Functional Requirements

| ID | Name |
|----|------|
| REQ-001 | a |
| REQ-002 | b |
| REQ-003 | c |
"""


class TestMatrixRefExistence:
    def test_missing_ref_flagged(self, tmp_path):
        code = tmp_path / "code"
        _write(str(code / "models" / "a.py"), "x")
        _write(str(code / "tests" / "test_a.py"), "x")
        _write(str(code / "tests" / "test_b.py"), "x")
        # models/missing.py NOT created → REQ-002 code_ref missing.
        out = check_matrix_refs(_MATRIX, code)
        assert "REQ-002" in out["missing_code_ref"]
        assert "REQ-001" not in out["missing_code_ref"]
        assert out["missing_test_ref"] == {}

    def test_no_code_dir_returns_empty(self):
        out = check_matrix_refs(_MATRIX, None)
        assert out == {"missing_code_ref": {}, "missing_test_ref": {}}


class TestVerify:
    def test_clean_when_all_present(self, tmp_path):
        code = tmp_path / "code"
        _write(str(code / "models" / "a.py"), "x")
        _write(str(code / "models" / "missing.py"), "x")  # now present
        _write(str(code / "tests" / "test_a.py"), "x")
        _write(str(code / "tests" / "test_b.py"), "x")
        # D-02 with only the two matrix REQs so completeness is clean too.
        d02 = _D02.replace("| REQ-003 | c |\n", "")
        res = verify(_MATRIX, d02_text=d02, code_dir=code)
        assert res["verified"] is True
        assert "missing_code_ref" not in res

    def test_missing_from_matrix_flagged(self, tmp_path):
        code = tmp_path / "code"
        _write(str(code / "models" / "a.py"), "x")
        _write(str(code / "models" / "missing.py"), "x")
        _write(str(code / "tests" / "test_a.py"), "x")
        _write(str(code / "tests" / "test_b.py"), "x")
        res = verify(_MATRIX, d02_text=_D02, code_dir=code)
        assert "REQ-003" in res["missing_from_matrix"]
        assert res["verified"] is False

    def test_nothing_to_check_not_green(self):
        # matrix only, no code_dir / d02 → nothing verifiable → not a meaningful green.
        res = verify(_MATRIX)
        assert res["verified"] is False
        assert "note" in res


class TestStaleCitation:
    def test_d27_stale_flagged(self, tmp_path):
        code = tmp_path / "code"
        _write(str(code / "models" / "a.py"), "x")
        _write(str(code / "models" / "missing.py"), "x")
        _write(str(code / "tests" / "test_a.py"), "x")
        _write(str(code / "tests" / "test_b.py"), "x")
        d27 = "# D-27\nBased on D-02 (v1.5) — old.\n"
        res = verify(_MATRIX, d02_text=_D02, code_dir=code, d27_text=d27)
        stale = res.get("stale_citations", [])
        assert any(s["doc"] == "D-02" and s["cited"] == "1.5" for s in stale)
        assert res["verified"] is False


@pytest.mark.skipif(not _FIXTURE.exists(), reason="TD.0 fixture not present")
class TestTD0Fixture:
    """The broken RCA case: verify-refs MUST surface drift + missing refs + stale."""

    def _paths(self):
        pa = _FIXTURE / "artifacts" / "planning-artifacts"
        return {
            "matrix": _FIXTURE / "artifacts" / "traceability" / "matrix.md",
            "d02": pa / "D-02-resource-plan-billable.md",
            "d19": pa / "D-19-opms" / "D-19-er-diagram.md",
            "d27": pa / "D-27-resource-plan-billable-test-spec.md",
            "code": _FIXTURE / "code",
        }

    def test_cli_catches_broken_case(self):
        p = self._paths()
        result = subprocess.run(
            [
                sys.executable, _SCRIPT,
                "--matrix", str(p["matrix"]),
                "--d02", str(p["d02"]),
                "--d19", str(p["d19"]),
                "--code-dir", str(p["code"]),
                "--d27", str(p["d27"]),
            ],
            capture_output=True, text=True, encoding="utf-8",
        )
        assert result.returncode == 1  # NOT a clean verify
        data = json.loads(result.stdout)
        assert data["verified"] is False
        # model drift: the v2.3 request/snapshot model never built in code.
        assert "resource.plan.request" in data["model_drift"]["design_only"]
        # matrix stuck at REQ-039 → 040/041/042 missing.
        assert any(r.endswith("-040") for r in data["missing_from_matrix"])
        # D-27 cites a stale D-02 version.
        assert any(s["doc"] == "D-02" for s in data["stale_citations"])
