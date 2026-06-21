#!/usr/bin/env python3
"""Tests for the U1 checks added to validate-implementation.py — spec-ref lint
(T1.2) and MODEL_DRIFT (T1.1).

Underscore-named so the canonical `python -m pytest` (default `test_*.py` pattern)
collects it; the sibling hyphenated `test-validate-implementation.py` only runs on
an explicit path. See the U1 note about the repo-wide hyphenated-collection gap.
"""

import os
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "validate_implementation",
    os.path.join(os.path.dirname(__file__), "..", "validate-implementation.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

check_spec_ref_leak = mod.check_spec_ref_leak
check_model_drift = mod.check_model_drift


def _w(d, name, body):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    return p


# --- T1.2 spec-ref lint ---

def test_spec_ref_leak_flagged(tmp_path):
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "m.py").write_text(
        "# implements REQ-FEAT-001\nx = 1  # TC-005\n", encoding="utf-8")
    issues = check_spec_ref_leak(str(tmp_path))
    assert len(issues) == 1
    assert issues[0]["type"] == "SPEC_REF_LEAK"
    assert issues[0]["count"] == 2
    assert issues[0]["path"] == "models/m.py"


def test_spec_ref_leak_clean(tmp_path):
    (tmp_path / "m.py").write_text("def f():\n    return 42\n", encoding="utf-8")
    assert check_spec_ref_leak(str(tmp_path)) == []


# --- T1.1 MODEL_DRIFT ---

_D19_DESIGN = """\
### Resource Plan
- **Tên vật lý (Physical name)**: `resource.plan`
### Resource Plan Request
- **Tên vật lý (Physical name)**: `resource.plan.request`
"""


def test_model_drift_design_only_flagged(tmp_path):
    design = _w(str(tmp_path), "D-19.md", _D19_DESIGN)
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "rp.py").write_text("_name = 'resource.plan'\n", encoding="utf-8")
    issues = check_model_drift(design, str(tmp_path))
    drift = [i for i in issues if i["type"] == "MODEL_DRIFT"]
    assert {i["token"] for i in drift} == {"resource.plan.request"}
    assert drift[0]["direction"] == "design_only"


def test_model_drift_excludes_wizard_from_rogue(tmp_path):
    design = _w(str(tmp_path), "D-19.md",
                "- **Physical name**: `resource.plan`\n- **Physical name**: `resource.plan.request`")
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "rp.py").write_text(
        "_name = 'resource.plan'\n_name = 'resource.plan.request'", encoding="utf-8")
    (tmp_path / "wizard").mkdir()
    (tmp_path / "wizard" / "wiz.py").write_text("_name = 'resource.plan.wizard'\n", encoding="utf-8")
    issues = check_model_drift(design, str(tmp_path))
    # wizard model is transient → not counted as a rogue code-only model
    assert [i for i in issues if i["type"] == "MODEL_DRIFT"] == []


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
