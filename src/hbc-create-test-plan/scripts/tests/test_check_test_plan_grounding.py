#!/usr/bin/env python3
"""Tests for check-test-plan-grounding.py (B9-1 no-fabricated-schedule / B9-4 technique-per-scope)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-test-plan-grounding.py")

# A plan whose schedule dates are all present in the D-02 source below, and whose
# in-scope rows each name a technique. Both English + VI sections appear so the
# language-aware section detection is exercised.
PLAN = """\
---
document_id: D-26
feature: "demo"
version: "2.0"
---

# Demo — Test Plan

## 2. Test Scope

### 2.1 In Scope

| Vùng | REQ | Trọng tâm test |
|---|---|---|
| Resource plan | REQ-001 | CRUD plan, unit + integration test |
| Đồng bộ allocation | REQ-010 | sync một chiều; integration test; xem D-27 |

### 2.2 Out of Scope

- Excel import wizard — không re-test.

## 7. Lịch trình (Schedule)

### 7.1 Mốc tiến độ

| Milestone | Target Date |
|-----------|-------------|
| D-27 hoàn tất | 2026-06-19 |
| Unit + integration xanh | 2026-07-01 |
"""

# Source doc that grounds both schedule dates.
SOURCE = "Lịch chốt 2026-06-19; unit + integration xong 2026-07-01."


def write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


def run(args: list[str]) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


def test_clean_when_dates_grounded_and_techniques_present():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", PLAN)
        src = write(tmp, "D-02.md", SOURCE)
        result, code = run([str(p), "--sources", str(src)])
        assert result["fabricated_dates"] == [], result["fabricated_dates"]
        assert result["technique_gaps"] == [], result["technique_gaps"]
        assert result["grounded"] is True
        assert result["valid"] is True
        assert code == 0


def test_fabricated_date_flagged_when_not_in_source():
    # source grounds only the first date; the second is fabricated
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", PLAN)
        src = write(tmp, "D-02.md", "Chỉ chốt 2026-06-19.")
        result, code = run([str(p), "--sources", str(src)])
        assert "2026-07-01" in result["fabricated_dates"], result["fabricated_dates"]
        assert "2026-06-19" not in result["fabricated_dates"]
        assert code == 1
        assert any(i["type"] == "FABRICATED_SCHEDULE" for i in result["issues"])


def test_no_sources_flags_all_concrete_dates():
    # no source corpus and no provisional marker → every concrete date is ungrounded
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", PLAN)
        result, code = run([str(p)])
        assert set(result["fabricated_dates"]) == {"2026-06-19", "2026-07-01"}
        assert result["grounded"] is False
        assert code == 1


def test_provisional_schedule_suppresses_fabrication():
    # an ASSUMPTION/pending marker in the schedule means dates are openly provisional
    plan = PLAN.replace(
        "### 7.1 Mốc tiến độ",
        "### 7.1 Mốc tiến độ\n\n> ASSUMPTION: lịch dự kiến, sẽ chốt sau Claude Design.",
    )
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", plan)
        result, code = run([str(p)])  # no sources at all
        assert result["fabricated_dates"] == [], result["fabricated_dates"]
        assert result["schedule_provisional"] is True
        assert code == 0


def test_no_schedule_section_is_no_fabrication():
    plan = PLAN.split("## 7. Lịch trình")[0]
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", plan)
        result, code = run([str(p)])
        assert result["fabricated_dates"] == []
        # technique_gaps still evaluated over the in-scope table


def test_technique_gap_flagged():
    # an in-scope row with no technique word and no D-27 link
    plan = PLAN.replace(
        "| Resource plan | REQ-001 | CRUD plan, unit + integration test |",
        "| Resource plan | REQ-001 | CRUD plan |",
    )
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", plan)
        src = write(tmp, "D-02.md", SOURCE)
        result, code = run([str(p), "--sources", str(src)])
        assert "Resource plan" in result["technique_gaps"], result["technique_gaps"]
        assert code == 1
        assert any(i["type"] == "TECHNIQUE_GAP" for i in result["issues"])


def test_d27_link_satisfies_technique_handoff():
    # a row with no technique word but a D-27 reference is NOT a gap
    plan = PLAN.replace(
        "| Resource plan | REQ-001 | CRUD plan, unit + integration test |",
        "| Resource plan | REQ-001 | xem D-27 |",
    )
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", plan)
        src = write(tmp, "D-02.md", SOURCE)
        result, code = run([str(p), "--sources", str(src)])
        assert "Resource plan" not in result["technique_gaps"]


def test_area_name_alone_does_not_self_satisfy():
    # the area NAME containing a technique word ('Unit') must NOT satisfy the row;
    # the evidence has to be in another column. No D-27 ref anywhere.
    plan = """\
# Demo — Test Plan

## 2. Test Scope

### 2.1 In Scope

| Area | REQ | Focus |
|------|-----|-------|
| Unit testing area | REQ-001 | CRUD plan |
"""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", plan)
        result, code = run([str(p)])
        assert "Unit testing area" in result["technique_gaps"], result["technique_gaps"]


def test_english_schedule_section_recognized():
    plan = PLAN.replace("## 7. Lịch trình (Schedule)", "## 7. Schedule")
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", plan)
        result, code = run([str(p)])
        assert set(result["fabricated_dates"]) == {"2026-06-19", "2026-07-01"}


def test_missing_source_is_loud_error():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", PLAN)
        result, code = run([str(p), "--sources", str(tmp / "nope.md")])
        assert code == 2
        assert "error" in result


def test_missing_plan_file():
    result, code = run(["/nonexistent/D-26.md"])
    assert code == 2
    assert "error" in result


def test_project_root_resolves_relative_paths():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        write(tmp, "D-26.md", PLAN)
        write(tmp, "D-02.md", SOURCE)
        result, code = run(["D-26.md", "--project-root", str(tmp), "--sources", "D-02.md"])
        assert "error" not in result
        assert result["grounded"] is True


def test_honest_verdict_fields():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        p = write(tmp, "D-26.md", PLAN)
        result, _ = run([str(p)])
        assert "structure_ok" in result
        assert result["semantic_review"] == "n/a"
        assert result["not_checked"]
        # B9-2 and B9-3 are explicitly delegated to the LLM/ASK layer
        joined = " ".join(result["not_checked"]).lower()
        assert "b9-2" in joined and "b9-3" in joined


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
