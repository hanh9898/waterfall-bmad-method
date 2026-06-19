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


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
