#!/usr/bin/env python3
"""Tests for trace-report.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "trace-report.py")


def run(matrix_path: str, extra_args: list[str] | None = None) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, "--matrix", matrix_path] + (extra_args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    data = json.loads(result.stdout) if result.stdout.strip() else {"error": result.stderr}
    return data, result.returncode


def test_full_matrix():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Traceability Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | US-01 | Entity_User | auth.py:login | TC-001 | PASSED | 2026-05-26 |\n"
            "| REQ-002 | US-02 | Entity_Order | order.py:create | TC-002 | PASSED | 2026-05-26 |\n"
        )
        data, code = run(str(matrix))
        assert data["total_requirements"] == 2
        assert data["fully_traced"] == 2
        assert data["fully_traced_pct"] == 100.0
        assert data["gaps"] == []
        assert code == 0


def test_matrix_with_gaps():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | Entity_User | auth.py | TC-001 | | |\n"
            "| REQ-002 | | | | | | |\n"
            "| REQ-003 | | Entity_Log | | TC-003 | | |\n"
        )
        data, code = run(str(matrix))
        assert data["total_requirements"] == 3
        assert data["coverage"]["design_ref"] == 2
        assert data["coverage"]["code_ref"] == 1
        assert data["coverage"]["test_ref"] == 2
        assert data["fully_traced"] == 1
        assert "REQ-002" in data["gaps"]
        assert "REQ-003" in data["gaps"]
        assert code == 0  # gaps are data, not errors


def test_strict_mode_exits_1_on_gaps():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | | | | | |\n"
        )
        _, code = run(str(matrix), ["--strict"])
        assert code == 1


def test_empty_matrix():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
        )
        data, code = run(str(matrix))
        assert data["total_requirements"] == 0
        assert data["fully_traced"] == 0
        assert code == 0


def test_missing_matrix_file():
    data, code = run("/nonexistent/matrix.md")
    assert "error" in data or "suggestion" in data
    assert code == 1


def test_output_to_file():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | D-19 | src/a.py | TC-001 | | |\n"
        )
        out = Path(tmp) / "report.json"
        run(str(matrix), ["-o", str(out)])
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["total_requirements"] == 1


def test_gap_details_structure():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | | | TC-001 | | |\n"
        )
        data, _ = run(str(matrix))
        assert len(data["gap_details"]) == 1
        gap = data["gap_details"][0]
        assert gap["req_id"] == "REQ-001"
        assert "design_ref" in gap["missing_columns"]
        assert "code_ref" in gap["missing_columns"]
        assert "test_ref" not in gap["missing_columns"]


def test_rollup_dedupes_shared_rows():
    # MEDIUM-9: a shared row (feature=shared) appears in EVERY feature matrix.
    # Roll-up must count it once (not once per feature) and keep it out of each
    # feature's own coverage denominator.
    M = ("| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
         "|---|---|---|---|---|---|---|---|\n")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        a = root / "features" / "auth" / "traceability"
        b = root / "features" / "report" / "traceability"
        a.mkdir(parents=True); b.mkdir(parents=True)
        (a / "matrix.md").write_text(
            M + "| auth | REQ-AUTH-001 | | D-19 | code | TC-001 | PASS | t |\n"
              + "| shared | REQ-SHARED-001 | | D-12 | code | TC-900 | PASS | t |\n", encoding="utf-8")
        (b / "matrix.md").write_text(
            M + "| report | REQ-REPORT-001 | | D-19 | | | | t |\n"
              + "| shared | REQ-SHARED-001 | | D-12 | code | TC-900 | PASS | t |\n", encoding="utf-8")
        cmd = [sys.executable, SCRIPT, "--rollup", str(root / "features" / "**" / "traceability" / "matrix.md")]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        data = json.loads(r.stdout)
        assert data["matrices_found"] == 2
        assert data["shared"]["total"] == 1          # REQ-SHARED-001 counted ONCE
        assert data["grand_total"] == 3              # auth(1) + report(1) + shared(1), not 4
        assert data["grand_fully_traced"] == 2       # auth + shared traced; report not
        feats = {f["feature"]: f for f in data["features"]}
        assert feats["auth"]["total"] == 1           # shared excluded from feature denominator
        assert feats["report"]["total"] == 1


if __name__ == "__main__":
    test_full_matrix()
    test_matrix_with_gaps()
    test_strict_mode_exits_1_on_gaps()
    test_empty_matrix()
    test_missing_matrix_file()
    test_output_to_file()
    test_gap_details_structure()
    test_rollup_dedupes_shared_rows()
    print("All trace-report tests passed.")


def test_d02_sync_detects_orphan_and_missing():
    # A-4: matrix has REQ-001, REQ-099 (orphan); D-02 defines REQ-001, REQ-002 (002 missing from matrix)
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | E | c | TC-1 | | |\n"
            "| REQ-099 | | E | c | TC-9 | | |\n"
        )
        d02 = Path(tmp) / "D-02.md"
        d02.write_text("## Yêu cầu chức năng\n\n| REQ ID |\n|---|\n| REQ-001 |\n| REQ-002 |\n")
        data, code = run(str(matrix), ["--d02", str(d02)])
        sync = data["d02_sync"]
        assert sync["in_sync"] is False
        assert "REQ-099" in sync["orphan_in_matrix"]
        assert "REQ-002" in sync["missing_from_matrix"]


def test_d02_sync_in_sync_and_strict():
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | E | c | TC-1 | | |\n"
        )
        d02 = Path(tmp) / "D-02.md"
        d02.write_text("REQ-001 only\n")
        data, code = run(str(matrix), ["--d02", str(d02), "--strict"])
        assert data["d02_sync"]["in_sync"] is True
        assert code == 0


def test_d02_sync_multisegment_feature_code():
    # Regression: a multi-segment feature code (slug `resource-plan-billable` →
    # REQ-RESOURCE-PLAN-BILLABLE-001) must be recognized. The old single-segment
    # regex read 0 REQs from D-02 and flagged every matrix row as a false orphan.
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|---------|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| resource-plan-billable | REQ-RESOURCE-PLAN-BILLABLE-001 | | E | c | TC-1 | | |\n"
        )
        d02 = Path(tmp) / "D-02.md"
        d02.write_text(
            "## Yêu cầu chức năng\n\n| REQ ID | Mô tả |\n|---|---|\n"
            "| REQ-RESOURCE-PLAN-BILLABLE-001 | Billable plan |\n"
        )
        data, code = run(str(matrix), ["--d02", str(d02), "--strict"])
        sync = data["d02_sync"]
        assert sync["in_sync"] is True, sync
        assert sync["d02_req_count"] == 1, sync
        assert code == 0


def test_d02_sync_ignores_prose_req_refs():
    # F2: a REQ mentioned only in D-02 prose must NOT count as a defined requirement
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | E | c | TC-1 | | |\n"
        )
        d02 = Path(tmp) / "D-02.md"
        d02.write_text(
            "## Giả định\nREQ-999 sẽ làm ở v2.\n\n"
            "## Yêu cầu chức năng\n\n| REQ ID | Mô tả |\n|---|---|\n| REQ-001 | Login |\n"
        )
        data, code = run(str(matrix), ["--d02", str(d02), "--strict"])
        sync = data["d02_sync"]
        assert sync["in_sync"] is True, sync          # REQ-999 (prose) not counted
        assert "REQ-999" not in sync["missing_from_matrix"]
        assert code == 0


def test_d02_sync_empty_table_does_not_fall_back_to_prose():
    # F2 (re-review): functional section present but table empty (draft) + prose REQ-999
    # → REQ-999 must NOT be counted as defined (no whole-file fallback when section exists)
    with tempfile.TemporaryDirectory() as tmp:
        matrix = Path(tmp) / "matrix.md"
        matrix.write_text(
            "# Matrix\n\n"
            "| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |\n"
            "|--------|----------|------------|----------|----------|-------------|----------|\n"
            "| REQ-001 | | E | c | TC-1 | | |\n"
        )
        d02 = Path(tmp) / "D-02.md"
        d02.write_text(
            "## Giả định\nREQ-999 dự kiến làm sau.\n\n"
            "## Yêu cầu chức năng\n\n| REQ ID | Mô tả |\n|---|---|\n"  # header + separator, NO data rows
        )
        data, _ = run(str(matrix), ["--d02", str(d02)])
        sync = data["d02_sync"]
        assert "REQ-999" not in sync["missing_from_matrix"], sync
        assert sync["missing_from_matrix"] == []         # nothing defined yet
        assert "REQ-001" in sync["orphan_in_matrix"]     # matrix-only
