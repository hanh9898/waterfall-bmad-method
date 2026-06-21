#!/usr/bin/env python3
"""Tests for check-readiness.py (P-1)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-readiness.py")

D02 = """\
# D-02

## Yêu cầu chức năng

| REQ ID | Mô tả |
|--------|-------|
| REQ-001 | Login |
| REQ-002 | Order |
"""


def _w(d: Path, name: str, body: str) -> str:
    p = d / name
    p.write_text(body, encoding="utf-8")
    return str(p)


def run(args: list[str]) -> tuple[dict, int]:
    r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


def _d27(*reqs: str) -> str:
    """Minimal TC-scoped D-27: one `### TC-` block per REQ id (or pass a single
    comma-joined string for a multi-REQ TC). D-27 coverage is now TC-bound (#3)."""
    blocks = "\n".join(
        f"### TC-{i:03d}: case\n**REQ ID:** {r}\n" for i, r in enumerate(reqs, 1)
    )
    return "## Detailed Test Cases\n\n" + blocks


def test_ready_all_covered():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", _d27("REQ-001", "REQ-002"))
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["ready"] is True
        assert data["uncovered_by_test"] == []
        # honest-verdict contract (S-3): assert the full shape, not just `ready`.
        assert data["structure_ok"] is True
        assert data["semantic_review"] == "n/a"
        assert data["passed"] is True
        assert "D-27" in data["checked_documents"]
        assert code == 0


def test_uncovered_by_test():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", _d27("REQ-001"))  # REQ-002 has no TC
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["ready"] is False
        assert data["uncovered_by_test"] == ["REQ-002"]
        assert code == 1


def test_orphan_downstream():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", _d27("REQ-001", "REQ-002", "REQ-099"))  # REQ-099 not in D-02
        data, code = run(["--d02", d02, "--d27", d27])
        assert "REQ-099" in data["orphan_reqs_downstream"]
        assert data["ready"] is False
        assert code == 1


def test_d26_gap_blocks_ready():
    # GAP-1: the D-26 (test plan) reconcile is gating but was untested.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d26 = _w(d, "D-26.md", "Plan covers REQ-001 only\n")  # REQ-002 missing
        data, code = run(["--d02", d02, "--d26", d26])
        assert "D-26" in data["checked_documents"]
        assert data["uncovered_by_plan"] == ["REQ-002"]
        assert data["ready"] is False
        assert code == 1


def test_d26_and_d27_independent_gaps():
    # GAP-9: D-27 clean but D-26 has a gap → still not ready, gap attributed to plan.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", _d27("REQ-001", "REQ-002"))
        d26 = _w(d, "D-26.md", "REQ-001\n")
        data, code = run(["--d02", d02, "--d27", d27, "--d26", d26])
        assert data["uncovered_by_test"] == []
        assert data["uncovered_by_plan"] == ["REQ-002"]
        assert data["ready"] is False
        assert code == 1


def test_orphan_via_d21_blocks_ready():
    # GAP-3: an orphan from informational D-21 still flags (undefined REQ is a seam).
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", _d27("REQ-001", "REQ-002"))
        d21 = _w(d, "D-21.md", "REQ-001 REQ-002 REQ-777\n")  # REQ-777 undefined
        data, code = run(["--d02", d02, "--d27", d27, "--d21", d21])
        assert "REQ-777" in data["orphan_reqs_downstream"]
        assert data["ready"] is False
        assert code == 1


def test_matrix_fully_covered_is_ready():
    # GAP-10: the matrix happy path (all REQs present) → ready.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        matrix = _w(d, "matrix.md", "| req_id |\n|---|\n| REQ-001 |\n| REQ-002 |\n")
        data, code = run(["--d02", d02, "--matrix", matrix])
        assert data["missing_from_matrix"] == []
        assert data["ready"] is True
        assert code == 0


def test_output_file_written():
    # GAP-2: --output writes JSON to a file (stdout then carries only a stderr note).
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", _d27("REQ-001", "REQ-002"))
        out = d / "report.json"
        r = subprocess.run(
            [sys.executable, SCRIPT, "--d02", d02, "--d27", d27, "-o", str(out)],
            capture_output=True, text=True,
        )
        assert r.returncode == 0
        assert out.exists()
        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["ready"] is True


def test_matrix_missing_req():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        matrix = _w(d, "matrix.md", "| req_id |\n|---|\n| REQ-001 |\n")  # REQ-002 missing
        data, code = run(["--d02", d02, "--matrix", matrix])
        assert data["missing_from_matrix"] == ["REQ-002"]
        assert data["ready"] is False
        assert code == 1


def test_prose_req_in_d02_not_counted_as_defined():
    # D-02 prose mentions REQ-900 outside the functional table → not "defined"
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", "## Giả định\nREQ-900 sau.\n\n" + D02)
        d27 = _w(d, "D-27.md", _d27("REQ-001", "REQ-002"))  # does NOT cover REQ-900
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["d02_req_count"] == 2  # only REQ-001, REQ-002
        assert data["ready"] is True       # REQ-900 was never "defined"


def test_d02_missing_file_exit_2():
    r = subprocess.run([sys.executable, SCRIPT, "--d02", "/nope/D-02.md"], capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2
    assert "error" in json.loads(r.stdout)


def test_d02_no_functional_section_exit_2():
    # D4: absent functional section is an error, NOT a whole-file fallback —
    # prose REQ ids must never be promoted to the authoritative "defined" set.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", "# D-02\n\n## Giả định\nREQ-900 sẽ làm sau.\n")
        d27 = _w(d, "D-27.md", "REQ-900\n")
        data, code = run(["--d02", d02, "--d27", d27])
        assert code == 2
        assert "error" in data
        assert data["ready"] is False
        # M3: error result keeps the full verdict shape (no KeyError for callers).
        assert data["structure_ok"] is False
        assert data["passed"] is False
        assert data["checked_documents"] == []


def test_empty_req_id_does_not_falsely_bind_next_field():
    # CRITICAL (C1): a TC with an EMPTY **REQ ID:** followed by a field mentioning
    # another REQ must NOT bind that REQ, and must be surfaced as unbindable.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md",
                 _d27("REQ-001")
                 + "\n### TC-009: blank binding\n**REQ ID:**\n**Trace:** REQ-002 related\n")
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["uncovered_by_test"] == ["REQ-002"]  # REQ-002 NOT falsely covered
        assert data["tc_without_req_id"] == 1            # the blank TC is surfaced
        assert code == 1


def test_d21_uncovered_does_not_block_ready():
    # D2: a REQ absent from the API spec (e.g. UI/batch-only) is informational —
    # uncovered_by_api must NOT flip ready to False on its own.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", _d27("REQ-001", "REQ-002"))  # fully covered by test
        d21 = _w(d, "D-21.md", "REQ-001\n")           # REQ-002 has no API surface
        data, code = run(["--d02", d02, "--d27", d27, "--d21", d21])
        assert data["uncovered_by_api"] == ["REQ-002"]
        assert data["ready"] is True
        assert code == 0


def test_only_d02_is_not_a_meaningful_green():
    # P6: nothing reconciled → not ready (don't report a green that verified nothing).
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        data, code = run(["--d02", d02])
        assert data["checked_documents"] == []
        assert data["ready"] is False
        assert code == 1


def test_only_d21_informational_is_not_ready():
    # P6+D2 regression: D-21 alone is informational/non-gating — a run that
    # reconciled ONLY D-21 verified nothing that can fail and must not be green.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d21 = _w(d, "D-21.md", "REQ-001 REQ-002\n")  # even fully-mentioned
        data, code = run(["--d02", d02, "--d21", d21])
        assert data["checked_documents"] == ["D-21"]
        assert data["ready"] is False
        assert code == 1


def test_d27_bare_mention_not_counted_as_covered():
    # #3: a D-27 that only MENTIONS the REQ ids (e.g. a pasted requirements
    # appendix) with NO `### TC-` block must NOT count as covered.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", "## Appendix\n\nThis spec relates to REQ-001 and REQ-002.\n")
        data, code = run(["--d02", d02, "--d27", d27])
        assert sorted(data["uncovered_by_test"]) == ["REQ-001", "REQ-002"]
        assert data["ready"] is False
        assert code == 1


def test_d27_multi_req_single_tc():
    # #3 + D3: one TC block may bind several comma-separated REQ ids.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md", _d27("REQ-001, REQ-002"))  # one TC, two reqs
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["uncovered_by_test"] == []
        assert data["ready"] is True
        assert code == 0


def test_d27_h4_tc_heading_counted():
    # #2: a `#### TC-` (4-hash) detail heading must still bind its REQ.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md",
                 "## Detail\n\n#### TC-001: a\n**REQ ID:** REQ-001\n\n"
                 "#### TC-002: b\n**REQ ID:** REQ-002\n")
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["uncovered_by_test"] == []
        assert data["ready"] is True


def test_d27_tc_inside_code_fence_not_counted():
    # #3: a `### TC-` inside a ``` fence is an example, not a real test case.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        body = ("## Detail\n\n```\n### TC-001: example\n**REQ ID:** REQ-001\n```\n\n"
                + _d27("REQ-002"))  # only REQ-002 is a real TC
        d27 = _w(d, "D-27.md", body)
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["uncovered_by_test"] == ["REQ-001"]  # fenced TC does not count
        assert code == 1


def test_d27_req_id_wrapped_to_next_line():
    # #4: REQ id wrapped onto the line below the marker is still read.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md",
                 "## Detail\n\n### TC-001: a\n**REQ ID:**\nREQ-001\n\n"
                 "### TC-002: b\n**REQ ID:** REQ-002\n")
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["uncovered_by_test"] == []
        assert data["ready"] is True


def test_d27_tc_without_req_id_surfaced():
    # #1: a TC block with no **REQ ID:** is reported, not silently ignored.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md",
                 _d27("REQ-001", "REQ-002")
                 + "\n### TC-099: orphaned\n**Category:** Functional\n")
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["tc_without_req_id"] == 1
        assert data["ready"] is True  # the two real REQs are still covered


D02_NS = """\
# D-02

## Yêu cầu chức năng

| REQ ID | Mô tả |
|--------|-------|
| REQ-AUTH-001 | Login |
| REQ-AUTH-002 | Logout |
"""


def test_feature_namespaced_ids_covered():
    # v2 false-green regression guard: namespaced REQ-<FEAT>-NNN ids must be
    # DEFINED + reconciled. A bare `REQ-\d{3,}` regex matched zero of these →
    # d02_req_count:0 → ready:true for everything (the seam bug).
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02_NS)
        d27 = _w(d, "D-27.md", _d27("REQ-AUTH-001", "REQ-AUTH-002"))
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["d02_req_count"] == 2          # ids were actually parsed
        assert data["ready"] is True
        assert data["uncovered_by_test"] == []
        assert code == 0


def test_feature_namespaced_gap_detected():
    # The one a false-green would hide: a defined namespaced REQ with no TC must
    # be reported uncovered (not silently green).
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02_NS)
        d27 = _w(d, "D-27.md", _d27("REQ-AUTH-001"))  # 002 missing
        data, code = run(["--d02", d02, "--d27", d27])
        assert data["d02_req_count"] == 2
        assert data["uncovered_by_test"] == ["REQ-AUTH-002"]
        assert data["ready"] is False
        assert code == 1


# --- DF-9: matrix test_ref ↔ D-27 drift gates readiness ---

_MATRIX_HDR = (
    "| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
    "|---|---|---|---|---|---|---|---|\n"
)


def test_stale_matrix_test_ref_blocks_ready():
    # The DF-9 seam: D-02/D-27/matrix all list the same REQs (so the existing
    # uncovered_by_test and missing_from_matrix checks are clean), yet the matrix
    # test_ref is STALE — D-27 bound TC-044 to REQ-002 but the matrix never got it.
    # IR must catch the drift and refuse to close Phase 2.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md",
                 "## Detail\n\n### TC-001: a\n**REQ ID:** REQ-001\n\n"
                 "### TC-002: b\n**REQ ID:** REQ-002\n\n"
                 "#### TC-044: cascade case\n**REQ ID:** REQ-002\n")
        matrix = _w(d, "matrix.md",
                    _MATRIX_HDR
                    + "| f | REQ-001 | | D | c | TC-001 | | |\n"
                    + "| f | REQ-002 | | D | c | TC-002 | | |\n")  # missing TC-044
        data, code = run(["--d02", d02, "--d27", d27, "--matrix", matrix])
        assert data["uncovered_by_test"] == []          # every REQ has a TC
        assert data["missing_from_matrix"] == []         # every REQ has a row
        assert data["test_ref_drift"]["REQ-002"]["missing"] == ["TC-044"]
        assert data["ready"] is False                    # but the matrix is stale
        assert code == 1


def test_matrix_test_ref_in_sync_is_ready():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d27 = _w(d, "D-27.md",
                 "## Detail\n\n### TC-001: a\n**REQ ID:** REQ-001\n\n"
                 "### TC-002: b\n**REQ ID:** REQ-002\n")
        matrix = _w(d, "matrix.md",
                    _MATRIX_HDR
                    + "| f | REQ-001 | | D | c | TC-001 | | |\n"
                    + "| f | REQ-002 | | D | c | TC-002 | | |\n")
        data, code = run(["--d02", d02, "--d27", d27, "--matrix", matrix])
        assert "test_ref_drift" not in data              # in sync → key absent
        assert data["ready"] is True
        assert code == 0


# --- B13-1: matrix trace-column non-empty ---

def test_matrix_row_present_but_blank_code_ref_blocks_ready():
    # B13-1: a REQ can have a matrix ROW yet a blank code_ref — still untraced for
    # that axis. The "39/39 green that hid empty cells" failure.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        matrix = _w(d, "matrix.md",
                    _MATRIX_HDR
                    + "| f | REQ-001 | | D | c1 | TC-001 | | |\n"
                    + "| f | REQ-002 | | D |    | TC-002 | | |\n")  # blank code_ref
        data, code = run(["--d02", d02, "--matrix", matrix])
        assert data["missing_from_matrix"] == []          # both have a row
        assert data["matrix_coverage_gaps"]["REQ-002"] == ["code_ref"]
        assert data["ready"] is False
        assert code == 1


# --- B13-2: 3-way REQ ↔ TASK ↔ design reconcile ---

_TB_HDR = "| task_id | description | design_ref | test_refs |\n|---|---|---|---|\n"


def test_req_without_task_blocks_ready():
    # B13-2(a): a defined REQ with no task in the task-breakdown.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        tb = _w(d, "tb.md", _TB_HDR + "| TASK-001 | covers REQ-001 | m | TC-001 |\n")
        data, code = run(["--d02", d02, "--task-breakdown", tb])
        assert data["reqs_without_task"] == ["REQ-002"]
        assert "task-breakdown" in data["checked_documents"]
        assert data["ready"] is False
        assert code == 1


def test_orphan_task_blocks_ready():
    # B13-2(b): a task for a REQ no longer defined in D-02 (stale slice).
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        tb = _w(d, "tb.md",
                _TB_HDR
                + "| TASK-001 | REQ-001 | m | TC-001 |\n"
                + "| TASK-002 | REQ-002 | m | TC-002 |\n"
                + "| TASK-003 | REQ-099 stale | m | TC-099 |\n")  # REQ-099 undefined
        data, code = run(["--d02", d02, "--task-breakdown", tb])
        assert data["orphan_tasks"] == ["REQ-099"]
        assert data["ready"] is False
        assert code == 1


def test_task_breakdown_all_reqs_tasked_is_ready():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        tb = _w(d, "tb.md",
                _TB_HDR
                + "| TASK-001 | REQ-001 | m | TC-001 |\n"
                + "| TASK-002 | REQ-002 | m | TC-002 |\n")
        data, code = run(["--d02", d02, "--task-breakdown", tb])
        assert data["reqs_without_task"] == []
        assert data["orphan_tasks"] == []
        assert data["ready"] is True
        assert code == 0


# --- B13-2 / B13-4: version-coherence at the seam ---

def test_stale_d02_citation_in_d26_blocks_ready():
    # B13-4: D-26 cites D-02 v2.2 while D-02 frontmatter declares v2.3.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", "---\nversion: \"2.3\"\n---\n" + D02)
        d26 = _w(d, "D-26.md", "Scope per D-02 (v2.2).\nREQ-001 REQ-002\n")  # stale cite
        data, code = run(["--d02", d02, "--d26", d26])
        assert data["uncovered_by_plan"] == []            # coverage is fine
        srcs = [s["source"] for s in data["stale_citations"]]
        assert "D-26" in srcs
        assert data["stale_citations"][0]["cited"] == "2.2"
        assert data["stale_citations"][0]["declared"] == "2.3"
        assert data["ready"] is False
        assert code == 1


def test_stale_d02_citation_in_task_breakdown_blocks_ready():
    # B13-2(c): the half-failure — task-breakdown sources pin a stale D-02 version.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", "---\nversion: \"2.3\"\n---\n" + D02)
        tb = _w(d, "tb.md",
                "sources:\n  - D-02 v1.8 (39 REQ)\n\n"
                + _TB_HDR
                + "| TASK-001 | REQ-001 | m | TC-001 |\n"
                + "| TASK-002 | REQ-002 | m | TC-002 |\n")
        data, code = run(["--d02", d02, "--task-breakdown", tb])
        assert data["reqs_without_task"] == []            # both REQs have a task
        srcs = [s["source"] for s in data["stale_citations"]]
        assert "task-breakdown" in srcs
        assert data["ready"] is False                     # but it's built on stale D-02
        assert code == 1


def test_matching_d02_version_citation_is_ready():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", "---\nversion: \"2.3\"\n---\n" + D02)
        d26 = _w(d, "D-26.md", "Scope per D-02 (v2.3).\nREQ-001 REQ-002\n")
        data, code = run(["--d02", d02, "--d26", d26])
        assert "stale_citations" not in data
        assert data["ready"] is True
        assert code == 0


# --- B13-3: model-level code ↔ design drift ---

_D19 = """\
# D-19

- **Tên vật lý (Physical name)**: `widget.request`
- **Tên vật lý (Physical name)**: `widget_line`
"""


def test_model_drift_design_only_blocks_ready():
    # B13-3: D-19 declares widget.request but the code never defines it.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d19 = _w(d, "D-19.md", _D19)
        codedir = d / "code"
        models = codedir / "models"
        models.mkdir(parents=True)
        (models / "widget_line.py").write_text(
            "class WidgetLine(models.Model):\n    _name = 'widget_line'\n", encoding="utf-8")
        # NOTE: widget.request is NOT defined in code → drift.
        data, code = run(["--d02", d02, "--d19", d19, "--code-dir", str(codedir)])
        assert data["model_drift"]["design_only"] == ["widget.request"]
        assert "D-19/code" in data["checked_documents"]
        assert data["ready"] is False
        assert code == 1


def test_model_in_sync_is_ready():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d19 = _w(d, "D-19.md", _D19)
        codedir = d / "code"
        models = codedir / "models"
        models.mkdir(parents=True)
        (models / "m.py").write_text(
            "class A(models.Model):\n    _name = 'widget.request'\n\n"
            "class B(models.Model):\n    _name = 'widget_line'\n", encoding="utf-8")
        data, code = run(["--d02", d02, "--d19", d19, "--code-dir", str(codedir)])
        assert "model_drift" not in data
        assert data["ready"] is True
        assert code == 0


def test_d19_without_code_dir_skips_drift_no_false_green():
    # B13-3 half-pair guard: --d19 alone must NOT register a green "D-19/code" check.
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d19 = _w(d, "D-19.md", _D19)
        d27 = _w(d, "D-27.md", _d27("REQ-001", "REQ-002"))
        data, code = run(["--d02", d02, "--d27", d27, "--d19", d19])
        assert "D-19/code" not in data["checked_documents"]  # drift skipped
        assert "model_drift" not in data
        assert data["ready"] is True                          # D-27 still gating
        assert code == 0


def test_missing_code_dir_skips_drift():
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02)
        d19 = _w(d, "D-19.md", _D19)
        d27 = _w(d, "D-27.md", _d27("REQ-001", "REQ-002"))
        data, code = run(["--d02", d02, "--d27", d27, "--d19", d19, "--code-dir", str(d / "nope")])
        assert "D-19/code" not in data["checked_documents"]
        assert data["ready"] is True
        assert code == 0


# --- masking / false-positive regression (bare vs canonical id form) ---

D02_FEAT = """\
# D-02

## Yêu cầu chức năng

| REQ ID | Mô tả |
|--------|-------|
| REQ-FEAT-001 | Login |
| REQ-FEAT-002 | Order |
"""


def test_bare_form_downstream_reconciles_with_canonical_d02():
    # Masking-bug regression: D-02 defines canonical REQ-FEAT-NNN; the matrix/plan
    # write the SAME requirements in bare form REQ-NNN. They must reconcile by
    # trailing number, NOT be flagged as uncovered/orphan (exact-string set diff bug).
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        d02 = _w(d, "D-02.md", D02_FEAT)
        d26 = _w(d, "D-26.md", "Plan covers REQ-001 and REQ-002.\n")  # bare form
        matrix = _w(d, "matrix.md", "| req_id |\n|---|\n| REQ-001 |\n| REQ-002 |\n")  # bare
        data, code = run(["--d02", d02, "--d26", d26, "--matrix", matrix])
        assert data["uncovered_by_plan"] == []
        assert data["missing_from_matrix"] == []
        assert data["orphan_reqs_downstream"] == []   # not false orphans
        assert data["ready"] is True
        assert code == 0


# --- TD.0 fixture regression: the gate MUST fail the known-broken case ---

_FIXTURE = (
    Path(__file__).resolve().parents[4]
    / "process-review" / "fixtures" / "resource-plan-billable"
)


def test_td0_broken_fixture_is_blocked():
    """The whole point of the overhaul: the gate must now FAIL the RCA error-state
    fixture it once let through, surfacing the half-failure with the right reasons.
    """
    pa = _FIXTURE / "artifacts" / "planning-artifacts"
    if not pa.exists():
        import pytest
        pytest.skip("TD.0 fixture not present")
    args = [
        "--d02", str(pa / "D-02-resource-plan-billable.md"),
        "--d27", str(pa / "D-27-resource-plan-billable-test-spec.md"),
        "--d26", str(pa / "D-26-resource-plan-billable-test-plan.md"),
        "--matrix", str(_FIXTURE / "artifacts" / "traceability" / "matrix.md"),
        "--task-breakdown", str(_FIXTURE / "artifacts" / "implementation-artifacts" / "task-breakdown.md"),
        "--d19", str(pa / "D-19-opms" / "D-19-er-diagram.md"),
        "--code-dir", str(_FIXTURE / "code"),
    ]
    data, code = run(args)
    assert data["ready"] is False
    assert code == 1
    # B13-1: REQ-040/041/042 have no matrix row.
    assert [r[-3:] for r in data["missing_from_matrix"]] == ["040", "041", "042"]
    # B13-2: the request/snapshot/withdraw slice has no task.
    assert all(r in {x[-3:] for x in data["reqs_without_task"]} for r in ("040", "041", "042"))
    # B13-2/B13-4: D-26/D-27/task-breakdown all cite a stale D-02 version.
    srcs = {s["source"] for s in data["stale_citations"]}
    assert {"D-26", "D-27", "task-breakdown"} <= srcs
    # B13-3: code stayed on the old model; the Request+Snapshot models are design-only.
    assert data["model_drift"]["design_only"] == ["resource.plan.request", "resource.plan.request.line"]
    # No FALSE positives: bare/canonical forms reconciled, so no false orphans/uncovered.
    assert data["orphan_tasks"] == []
    assert data["orphan_reqs_downstream"] == []
    assert data["uncovered_by_plan"] == []
    assert data["uncovered_by_test"] == []


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
