#!/usr/bin/env python3
"""Tests for the shared hbc_validation library (Đợt 0)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import hbc_validation as hv  # noqa: E402


# --- verdict (S-3 honest verdict) ---

def test_verdict_structural_only_passes():
    v = hv.verdict(True, semantic_review=hv.SEMANTIC_NA, checked=["a"], not_checked=["b"])
    assert v["structure_ok"] is True
    assert v["semantic_review"] == "n/a"
    assert v["passed"] is True
    assert v["checked"] == ["a"]
    assert v["not_checked"] == ["b"]


def test_verdict_pending_blocks_pass():
    v = hv.verdict(True, semantic_review=hv.SEMANTIC_PENDING)
    assert v["structure_ok"] is True
    assert v["passed"] is False  # chưa review ⟹ chưa pass


def test_verdict_structure_fail():
    v = hv.verdict(False, semantic_review=hv.SEMANTIC_NA)
    assert v["passed"] is False


def test_verdict_defaults_na_and_empty_lists():
    v = hv.verdict(True)
    assert v["semantic_review"] == "n/a"
    assert v["checked"] == [] and v["not_checked"] == []
    assert v["passed"] is True


# --- find_section (config language, no hardcoded Japanese) ---

def test_find_section_by_configured_label():
    content = "## Phạm vi\n\nnội dung"
    assert hv.find_section(content, "Scope", "Phạm vi") is not None


def test_find_section_by_english_canonical():
    content = "## 2. Scope (boundaries)\n\nx"
    assert hv.find_section(content, "Scope", "Phạm vi") is not None


def test_find_section_not_found():
    assert hv.find_section("## Other\n\nx", "Scope", "Phạm vi") is None


def test_find_section_ignores_empty_labels():
    assert hv.find_section("## Scope\n", "Scope", None, "") is not None


# --- parse_table + extract_column (S-4: chỉ tin ô bảng) ---

TABLE_DOC = """\
## Yêu cầu chức năng

| REQ ID | Category | Requirement |
|--------|----------|-------------|
| REQ-001 | Auth | login |
| REQ-002 | Order | create |

## Phần khác

REQ-001 được nhắc lại ở prose nhưng KHÔNG phải định nghĩa.
"""


def test_parse_table_returns_data_rows_only():
    rows = hv.parse_table(TABLE_DOC, "Functional Requirements", "Yêu cầu chức năng")
    assert len(rows) == 2
    assert rows[0][0] == "REQ-001"
    assert rows[1][0] == "REQ-002"


def test_parse_table_missing_section():
    assert hv.parse_table(TABLE_DOC, "Nonexistent") == []


def test_extract_column():
    rows = hv.parse_table(TABLE_DOC, "Yêu cầu chức năng")
    assert hv.extract_column(rows, 0) == ["REQ-001", "REQ-002"]


def test_extract_column_out_of_range_is_safe():
    rows = [["a", "b"], ["c"]]
    assert hv.extract_column(rows, 1) == ["b"]  # bỏ qua hàng thiếu ô


# --- regression patches from review ---

def test_parse_table_collects_all_subtables_without_header_bleed():
    # F1: a section with multiple sub-tables contributes ALL data rows, and the
    # second table's HEADER row must NOT leak in as data.
    doc = """\
## Yêu cầu chức năng

### 4.1

| REQ ID | Cat |
|--------|-----|
| REQ-001 | A |

### 4.2

| REQ ID | Cat |
|--------|-----|
| REQ-002 | B |
"""
    rows = hv.parse_table(doc, "Yêu cầu chức năng")
    assert rows == [["REQ-001", "A"], ["REQ-002", "B"]]


def test_parse_table_row_without_trailing_pipe():
    doc = "## S\n\n| A | B |\n|---|---|\n| x | y\n"
    rows = hv.parse_table(doc, "S")
    assert rows == [["x", "y"]]  # last cell not dropped


def test_find_section_skips_subsection_match():
    doc = """\
## 1. Tổng quan

### 1.1 Phạm vi và mục tiêu

overview

## 2. Phạm vi

real scope
"""
    m = hv.find_section(doc, "Scope", "Phạm vi")
    assert m is not None
    # must resolve to the real ## section, not the ### subsection
    assert "## 2. Phạm vi" in m.group(0)


def test_section_body_stops_at_same_level_heading():
    doc = "## A\n\nbody-a\n\n### A.1\n\nsub\n\n## B\n\nbody-b\n"
    m = hv.find_section(doc, "A")
    body = hv.section_body(doc, m)
    assert "body-a" in body and "sub" in body  # keeps own subsection
    assert "body-b" not in body  # stops at next ## B


# --- check_required_sections / section_has_content ---

def test_check_required_sections_all_present():
    doc = "## Overview\n\ntext\n\n## Bảo mật\n\nrules\n"
    issues = hv.check_required_sections(doc, [("Overview", "Tổng quan"), ("Security", "Bảo mật")])
    assert issues == []


def test_check_required_sections_missing_reports_canonical():
    doc = "## Overview\n\ntext\n"
    issues = hv.check_required_sections(doc, [("Overview", "Tổng quan"), ("Security", "Bảo mật")])
    assert len(issues) == 1
    assert issues[0]["type"] == "SECTION_MISSING"
    assert issues[0]["section"] == "Security"  # English canonical reported


def test_check_required_sections_empty():
    doc = "## Overview\n\n## Security\n\nx\n"
    issues = hv.check_required_sections(doc, [("Overview",), ("Security",)])
    empty = [i for i in issues if i["type"] == "SECTION_EMPTY"]
    assert len(empty) == 1 and empty[0]["section"] == "Overview"


def test_section_has_content_ignores_scaffolding():
    assert hv.section_has_content("| H |\n|---|\n") is False  # header+separator only
    assert hv.section_has_content("<!-- note -->") is False
    assert hv.section_has_content("real text") is True


# --- TC-block helpers (shared by readiness + facet engines) ---

def test_tc_field_same_line_and_wrapped():
    assert hv.tc_field("**REQ ID:** REQ-001\n", "REQ ID") == "REQ-001"
    assert hv.tc_field("**REQ ID:**\nREQ-001\n\n", "REQ ID") == "REQ-001"  # wrapped


def test_tc_field_empty_does_not_swallow_next_field():
    # CRITICAL regression: a bare **REQ ID:** must NOT absorb the next field's line
    # (else an empty binding would steal a later REQ id and falsely bind it).
    block = "**REQ ID:**\n**Trace:** REQ-555 related\n**Facets:** read\n"
    assert hv.tc_field(block, "REQ ID") == ""        # empty, not "**Trace:** ..."
    assert hv.tc_field(block, "Facets") == "read"


def test_tc_field_absent_is_none():
    assert hv.tc_field("**Facets:** read\n", "REQ ID") is None


def test_strip_code_fences_backtick_tilde_indented():
    assert "### TC-" not in hv.strip_code_fences("```\n### TC-9\n```\n")
    assert "### TC-" not in hv.strip_code_fences("~~~\n### TC-9\n~~~\n")          # tilde
    assert "### TC-" not in hv.strip_code_fences("    ```\n### TC-9\n    ```\n")  # indented
    assert "### TC-" not in hv.strip_code_fences("```python\n### TC-9\n```\n")   # info-string


def test_strip_code_fences_unclosed_is_failsafe():
    # Unclosed fence drops to EOF — fenced example never leaks as a real TC.
    assert "### TC-" not in hv.strip_code_fences("```\n### TC-9\n")


def test_strip_code_fences_keeps_real_content_after_block():
    assert "### TC-2" in hv.strip_code_fences("```\nx\n```\n### TC-2\n")


def test_iter_tc_blocks_levels_and_case():
    assert len(hv.iter_tc_blocks("### TC-1\nbody\n")) == 1
    assert len(hv.iter_tc_blocks("#### TC-1\nbody\n")) == 1        # 4-hash
    assert len(hv.iter_tc_blocks("###### TC-1\nbody\n")) == 1      # 6-hash
    assert len(hv.iter_tc_blocks("### tc-1\nbody\n")) == 1         # lowercase
    assert hv.iter_tc_blocks("```\n### TC-1\n```\n") == []         # fenced example


# --- tc_req_map / matrix_req_tc_map / test_ref_drift (DF-9 matrix staleness) ---

D27_DOC = """\
## Test Cases

### TC-001 — login happy path
**REQ ID:** REQ-AUTH-001
**Facets:** read

### TC-002 — lockout
**REQ ID:** REQ-AUTH-002, REQ-AUTH-001
**Facets:** write

#### TC-044 — new cascade case
**REQ ID:** REQ-AUTH-002

```
### TC-999 — fenced example, not real
**REQ ID:** REQ-AUTH-009
```
"""


def test_tc_req_map_inverts_tc_to_req():
    m = hv.tc_req_map(D27_DOC)
    assert m["REQ-AUTH-001"] == {"TC-001", "TC-002"}  # TC-002 names two REQs
    assert m["REQ-AUTH-002"] == {"TC-002", "TC-044"}  # 4-hash heading counted
    assert "REQ-AUTH-009" not in m  # fenced example never leaks


def test_matrix_req_tc_map_header_aware():
    matrix = """\
| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |
|---|---|---|---|---|---|---|---|
| auth | REQ-AUTH-001 | S-1 | D-06§1 | auth.py | TC-001, TC-002 | PASS | 2026-06-19 |
| auth | REQ-AUTH-002 | S-2 | D-06§2 | lock.py |  | | |
"""
    m = hv.matrix_req_tc_map(matrix)
    assert m["REQ-AUTH-001"] == {"TC-001", "TC-002"}
    assert m["REQ-AUTH-002"] == set()  # present row, empty test_ref


def test_matrix_req_tc_map_legacy_7col_no_feature():
    # No leading `feature` column — columns must be located by name, not position.
    matrix = """\
| req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |
|---|---|---|---|---|---|---|
| REQ-001 | S-1 | d | c | TC-005 | PASS | t |
"""
    assert hv.matrix_req_tc_map(matrix) == {"REQ-001": {"TC-005"}}


def test_test_ref_drift_reports_missing_and_stale():
    matrix = """\
| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |
|---|---|---|---|---|---|---|---|
| auth | REQ-AUTH-001 | S-1 | d | c | TC-001 | PASS | t |
| auth | REQ-AUTH-002 | S-2 | d | c | TC-002, TC-077 | PASS | t |
"""
    drift = hv.test_ref_drift(D27_DOC, matrix)
    # REQ-AUTH-001: D-27 binds {TC-001, TC-002}; matrix has only TC-001 → missing TC-002
    assert drift["REQ-AUTH-001"] == {"missing": ["TC-002"], "stale": []}
    # REQ-AUTH-002: D-27 binds {TC-002, TC-044}; matrix has {TC-002, TC-077}
    #   → missing TC-044 (in D-27, not in matrix), stale TC-077 (in matrix, not in D-27)
    assert drift["REQ-AUTH-002"] == {"missing": ["TC-044"], "stale": ["TC-077"]}


def test_test_ref_drift_empty_when_in_sync():
    matrix = """\
| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |
|---|---|---|---|---|---|---|---|
| auth | REQ-AUTH-001 | S-1 | d | c | TC-001, TC-002 | PASS | t |
| auth | REQ-AUTH-002 | S-2 | d | c | TC-002, TC-044 | PASS | t |
"""
    assert hv.test_ref_drift(D27_DOC, matrix) == {}


def test_test_ref_drift_ignores_req_absent_from_matrix():
    # A REQ bound in D-27 but with NO matrix row is NOT test_ref drift (it's the
    # matrix↔D-02 check's missing_from_matrix). Drift only covers REQs in the matrix.
    matrix = """\
| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | timestamp |
|---|---|---|---|---|---|---|---|
| auth | REQ-AUTH-001 | S-1 | d | c | TC-001, TC-002 | PASS | t |
"""
    assert hv.test_ref_drift(D27_DOC, matrix) == {}  # REQ-AUTH-002 absent → ignored


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
