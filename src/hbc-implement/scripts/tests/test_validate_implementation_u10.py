#!/usr/bin/env python3
"""Tests for the U10 checks added to validate-implementation.py — stale-design
block (B5-4) and DONE-sanity floor (B5-9).

Underscore-named so the canonical `python -m pytest` (default `test_*.py` pattern)
collects it; the sibling hyphenated file only runs on an explicit path.
"""

import os
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "validate_implementation",
    os.path.join(os.path.dirname(__file__), "..", "validate-implementation.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

check_design_stale = mod.check_design_stale
check_done_sanity = mod.check_done_sanity
validate = mod.validate


def _w(d, name, body):
    p = os.path.join(d, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    return p


_D19_V23 = '---\ndocument_id: D-19\nversion: "2.3"\n---\n# design\n`resource.plan`\n'
_D19_V13 = '---\ndocument_id: D-19\nversion: "1.3"\n---\n# design\n`resource.plan`\n'

_TASKS_CITES_V13 = """\
---
title: Task Breakdown
sources:
  - D-19 v1.3 (entities)
---
| task_id | description | design_ref | test_refs | priority | status | dependencies |
|---------|-------------|------------|-----------|----------|--------|--------------|
| TASK-001 | Model | resource_plan | TC-001 | 1 | done | - |
"""


# --- B5-4 DESIGN_STALE ---

def test_design_stale_flagged_when_breakdown_cites_old_version(tmp_path):
    d19 = _w(str(tmp_path), "D-19.md", _D19_V23)
    issues = check_design_stale(_TASKS_CITES_V13, [d19])
    stale = [i for i in issues if i["type"] == "DESIGN_STALE"]
    assert len(stale) == 1
    assert stale[0]["doc"] == "D-19"
    assert stale[0]["cited"] == "1.3"
    assert stale[0]["declared"] == "2.3"


def test_design_not_stale_when_versions_match(tmp_path):
    d19 = _w(str(tmp_path), "D-19.md", _D19_V13)  # live = 1.3, breakdown cites 1.3
    assert check_design_stale(_TASKS_CITES_V13, [d19]) == []


def test_design_stale_skips_unreadable_or_versionless(tmp_path):
    # A design path with no version cannot assert staleness — silent, not a crash.
    nover = _w(str(tmp_path), "D-19.md", "---\ndocument_id: D-19\n---\nno version\n")
    assert check_design_stale(_TASKS_CITES_V13, [nover]) == []
    # Missing file is skipped, not an error.
    assert check_design_stale(_TASKS_CITES_V13, [str(tmp_path / "absent.md")]) == []


def test_design_stale_uses_filename_doc_id_fallback(tmp_path):
    # No frontmatter document_id → bind by the D-NN in the filename.
    d19 = _w(str(tmp_path), "D-19-er-diagram.md", '---\nversion: "2.3"\n---\n`resource.plan`\n')
    issues = check_design_stale(_TASKS_CITES_V13, [d19])
    assert [i for i in issues if i["type"] == "DESIGN_STALE"]


# --- B5-9 DONE_NO_SANITY ---

_TASKS_DONE_WITH_TEST = """\
| task_id | description | design_ref | test_refs | priority | status | dependencies |
|---------|-------------|------------|-----------|----------|--------|--------------|
| TASK-001 | Model | resource_plan | TC-001 | 1 | done | - |
"""

_TASKS_DONE_NO_TEST = """\
| task_id | description | design_ref | test_refs | priority | status | dependencies |
|---------|-------------|------------|-----------|----------|--------|--------------|
| TASK-001 | Model | resource_plan | - | 1 | done | - |
| TASK-002 | TODO no test ok | x | - | 1 | todo | - |
"""


def test_done_sanity_clean_when_test_named():
    assert check_done_sanity(_TASKS_DONE_WITH_TEST) == []


def test_done_sanity_flags_done_without_test():
    issues = check_done_sanity(_TASKS_DONE_NO_TEST)
    assert [i for i in issues if i["type"] == "DONE_NO_SANITY"]
    # A TODO with no test is NOT flagged — only DONE rows.
    assert all(i["task_id"] == "TASK-001" for i in issues)


# --- wiring through validate() ---

def test_validate_wires_stale_and_sanity(tmp_path):
    d19 = _w(str(tmp_path), "D-19.md", _D19_V23)
    tasks = _w(str(tmp_path), "task-breakdown.md", _TASKS_CITES_V13)
    result = validate(tasks, stale_designs=[d19], require_sanity=True)
    assert result["valid"] is False
    assert any(i["type"] == "DESIGN_STALE" for i in result["issues"])
    # sanity floor passes here (TASK-001 names TC-001) — no false DONE_NO_SANITY
    assert not any(i["type"] == "DONE_NO_SANITY" for i in result["issues"])


def test_validate_no_stale_args_is_backcompat(tmp_path):
    # Without --stale-design / --require-sanity, behavior is unchanged (U1 baseline).
    tasks = _w(str(tmp_path), "task-breakdown.md", _TASKS_DONE_WITH_TEST)
    result = validate(tasks)
    assert result["valid"] is True


if __name__ == "__main__":
    import sys
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
