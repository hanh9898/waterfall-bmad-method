#!/usr/bin/env python3
"""Tests for check-behavioral-grounding.py (E-2 element↔REQ · T3.13d BDD · behavioral-vs-code drift · churn)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-behavioral-grounding.py")
REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE = REPO_ROOT / "process-review" / "fixtures" / "resource-plan-billable"

# A well-formed D-16: every element section names its REQ, has a BDD triad.
GOOD_DOC = """\
---
document_id: D-16
feature: "rpb"
version: "1.0"
semanticReview:
  status: pending
  openFacets: []
---

# RPB — Behavioral Design

## Overview

REQ-RPB-024 là state-machine 2 cấp; REQ-RPB-027 có invariant snapshot.

## REQ-RPB-024: Vòng đời 2 cấp

### State Transitions

| ID | From | Event | Guard | To | REQ |
|----|------|-------|-------|-----|-----|
| ST-01 | draft | submit | có ≥1 dòng | submitted | REQ-RPB-024 |
| ST-02 | submitted | submit | — | (illegal) | REQ-RPB-024 |

### BDD Scenarios

- Scenario (ST-01): Given draft với ≥1 dòng, When submit, Then submitted.

## REQ-RPB-027: Bất biến snapshot

### Invariants

| ID | Invariant | Enforcement point | REQ |
|----|-----------|-------------------|-----|
| INV-01 | snapshot không đổi sau submit | resource.plan write guard | REQ-RPB-027 |

## Revision History

| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | 2026-06-21 | T | Bản đầu |
"""


def run(args: list[str]) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


def _write(tmp: str, content: str) -> str:
    p = Path(tmp) / "D-16-rpb-behavioral-design.md"
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_good_doc_clean():
    with tempfile.TemporaryDirectory() as tmp:
        doc = _write(tmp, GOOD_DOC)
        result, code = run([doc, "--project-root", tmp])
        assert result["valid"] is True, result["issues"]
        assert code == 0
        assert result["bdd"]["has_triad"] is True


def test_untraced_element_section_flagged():
    # strip the REQ id from the heading AND rows of the ST section
    doc = GOOD_DOC.replace("## REQ-RPB-024: Vòng đời 2 cấp", "## Vòng đời 2 cấp")
    doc = doc.replace("| REQ-RPB-024 |", "| — |")
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(tmp, doc)
        result, code = run([path, "--project-root", tmp])
        assert any(i["type"] == "UNTRACED_ELEMENT_SECTION" for i in result["issues"]), result["issues"]
        assert code == 1


def test_parent_heading_traces_child_elements():
    # REQ named ONLY on the H2; child H3 has elements with no per-row REQ → still traced
    # via ancestor heading (the template's normal shape — no false UNTRACED).
    doc = """\
---
document_id: D-16
---
# X — Behavioral Design
## Overview
REQ-RPB-024 state-machine. Given a draft, When submit, Then submitted.
## REQ-RPB-024: Vòng đời
### State Transitions
| ID | From | Event | Guard | To |
|----|------|-------|-------|-----|
| ST-01 | draft | submit | ok | submitted |
## Revision History
| Version | Date | Author | Scope of Change |
|---------|------|--------|----------------|
| 1.0 | 2026-06-21 | T | init |
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(tmp, doc)
        result, code = run([path, "--project-root", tmp])
        assert result["untraced_element_sections"] == [], result["untraced_element_sections"]
        assert result["valid"] is True, result["issues"]


def test_vietnamese_bdd_triad_satisfies_gate():
    # A Vietnamese-only Giả sử / Khi / Thì triad must satisfy the BDD gate (no
    # hardcoded English-only requirement; document language is configurable).
    doc = GOOD_DOC.replace(
        "- Scenario (ST-01): Given draft với ≥1 dòng, When submit, Then submitted.",
        "- Kịch bản (ST-01): Giả sử plan ở draft, Khi người dùng submit, Thì chuyển sang submitted.",
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(tmp, doc)
        result, code = run([path, "--project-root", tmp])
        assert result["bdd"]["has_triad"] is True, result["bdd"]
        assert not any(i["type"] == "NO_BDD_SCENARIO" for i in result["issues"])


def test_no_bdd_scenario_flagged():
    doc = GOOD_DOC.replace(
        "- Scenario (ST-01): Given draft với ≥1 dòng, When submit, Then submitted.", ""
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(tmp, doc)
        result, code = run([path, "--project-root", tmp])
        assert result["bdd"]["has_triad"] is False
        assert any(i["type"] == "NO_BDD_SCENARIO" for i in result["issues"]), result["issues"]


def test_uncovered_req_from_sources():
    with tempfile.TemporaryDirectory() as tmp:
        doc = _write(tmp, GOOD_DOC)
        src = Path(tmp) / "D-02.md"
        # REQ-RPB-024/027 covered; REQ-RPB-099 is not in D-16 → uncovered (advisory)
        src.write_text("REQ-RPB-024 REQ-RPB-027 REQ-RPB-099", encoding="utf-8")
        result, code = run([doc, "--project-root", tmp, "--sources", str(src)])
        assert "REQ-RPB-099" in result["uncovered_reqs"], result["uncovered_reqs"]
        assert any(i["type"] == "UNCOVERED_REQ" for i in result["issues"])


def test_bare_and_canonical_req_reconcile():
    # D-16 uses canonical REQ-RPB-024; source uses bare REQ-024 → same trailing number.
    with tempfile.TemporaryDirectory() as tmp:
        doc = _write(tmp, GOOD_DOC)
        src = Path(tmp) / "D-02.md"
        src.write_text("REQ-024 REQ-027", encoding="utf-8")
        result, _ = run([doc, "--project-root", tmp, "--sources", str(src)])
        assert result["uncovered_reqs"] == [], result["uncovered_reqs"]


def test_behavior_drift_code_only():
    # Code defines a model the D-16 never names → code_only drift (the reliable D-16
    # signal: model_drift's design_only only fires from D-19-style "Physical name:"
    # lines, which a prose D-16 lacks — code_only is what grounds behaviour-vs-code).
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(tmp, GOOD_DOC)  # names resource.plan only
        codedir = Path(tmp) / "models"
        codedir.mkdir()
        (codedir / "m.py").write_text(
            "class A(models.Model):\n    _name = 'resource.plan'\n"
            "class B(models.Model):\n    _name = 'resource.plan.unmodeled'\n",
            encoding="utf-8",
        )
        result, code = run([path, "--project-root", tmp, "--code-dir", str(codedir)])
        assert "resource.plan.unmodeled" in result["behavior_drift"]["code_only"], result["behavior_drift"]
        assert "resource.plan" not in result["behavior_drift"]["code_only"]
        assert any(i["type"] == "BEHAVIOR_DRIFT_CODE_ONLY" for i in result["issues"])
        assert code == 1


def test_behavior_drift_design_only_via_physical_name_line():
    # design_only fires when a D-16 DOES carry a D-19-style physical-name line for a
    # model code never defines (supported but optional in D-16).
    doc = GOOD_DOC.replace(
        "## Revision History",
        "Physical name (Tên vật lý): `resource.plan.ghost`\n\n## Revision History",
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(tmp, doc)
        codedir = Path(tmp) / "models"
        codedir.mkdir()
        (codedir / "m.py").write_text(
            "class A(models.Model):\n    _name = 'resource.plan'\n", encoding="utf-8"
        )
        result, code = run([path, "--project-root", tmp, "--code-dir", str(codedir)])
        assert "resource.plan.ghost" in result["behavior_drift"]["design_only"], result["behavior_drift"]
        assert any(i["type"] == "BEHAVIOR_DRIFT_DESIGN_ONLY" for i in result["issues"])


def test_missing_code_dir_is_loud_error():
    with tempfile.TemporaryDirectory() as tmp:
        doc = _write(tmp, GOOD_DOC)
        result, code = run([doc, "--project-root", tmp, "--code-dir", str(Path(tmp) / "nope")])
        assert code == 2
        assert "error" in result


def test_missing_sources_is_loud_error():
    with tempfile.TemporaryDirectory() as tmp:
        doc = _write(tmp, GOOD_DOC)
        result, code = run([doc, "--project-root", tmp, "--sources", str(Path(tmp) / "nope.md")])
        assert code == 2
        assert "error" in result


def test_missing_document():
    result, code = run(["/nonexistent/D-16.md", "--project-root", "/tmp"])
    assert code == 2
    assert "error" in result


def test_churn_high_flag():
    extra = "".join(f"| 1.{i} | 2026-06-2{i} | T | e{i} |\n" for i in range(1, 7))
    doc = GOOD_DOC.replace(
        "| 1.0 | 2026-06-21 | T | Bản đầu |",
        "| 1.0 | 2026-06-21 | T | Bản đầu |\n" + extra,
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(tmp, doc)
        result, _ = run([path, "--project-root", tmp])
        assert result["churn"]["high_churn"] is True


# --- real-fixture eval (TD.0): grounding against the actual code models ---

def test_real_fixture_code_grounding():
    """A D-16 derived from the fixture's behaviour, grounded against the REAL code.

    The fixture has NO D-16 artifact (it predates D-16); this confirms the grounding
    check behaves on the fixture's behavioural code: a D-16 naming a stale model
    surfaces drift, while one naming only real models is clean against code.
    """
    if not FIXTURE.is_dir():
        return  # fixture not present in this checkout — skip silently
    code_dir = FIXTURE / "code" / "models"
    # D-16 names the real lifecycle model (resource.plan) → no design_only drift.
    doc = GOOD_DOC  # references resource.plan only
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(tmp, doc)
        result, _ = run([path, "--project-root", tmp, "--code-dir", str(code_dir)])
        assert "resource.plan" not in result["behavior_drift"]["design_only"], result["behavior_drift"]
        # the code defines line / line.month / summary the D-16 never models → code_only
        assert "resource.plan.summary" in result["behavior_drift"]["code_only"], result["behavior_drift"]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t(); print(f"  PASS  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL  {t.__name__}: {e}"); failed += 1
    print(f"\n{len(tests)-failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
