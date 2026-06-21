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


# ======================================================================
# Wave 1 / U1 — Đợt-1 anti-false-green primitives
# ======================================================================

# --- T1.5 matrix-coverage ---

_D02_REQS = """
REQ-FEAT-001 does a thing. Also REQ-FEAT-002 and the bare form REQ-003.
REQ-FEAT-040 / REQ-FEAT-041 / REQ-FEAT-042 are the late additions.
"""
_MATRIX_8COL = """
| feature | req_id | story_id | design_ref | code_ref | test_ref | gate_status | ts |
|---|---|---|---|---|---|---|---|
| feat | REQ-FEAT-001 |  | D-19 ent | src/a.py | TC-001 |  | 2026-01-01 |
| feat | REQ-FEAT-002 |  | D-19 ent | src/b.py | TC-002 |  | 2026-01-01 |
| feat | REQ-FEAT-003 |  |  |  |  |  | 2026-01-01 |
"""


def test_missing_from_matrix_catches_late_reqs():
    missing = hv.missing_from_matrix(_D02_REQS, _MATRIX_8COL)
    assert missing == ["REQ-FEAT-040", "REQ-FEAT-041", "REQ-FEAT-042"]


def test_missing_from_matrix_reconciles_bare_and_canonical():
    # bare REQ-003 in D-02 ↔ canonical REQ-FEAT-003 in matrix → identity by number
    assert "REQ-003" not in hv.missing_from_matrix(_D02_REQS, _MATRIX_8COL)


def test_req_num_map_reports_multiple_slugs():
    _, slugs = hv.req_num_map("REQ-ALPHA-001 and REQ-BETA-001")
    assert slugs == {"REQ-ALPHA", "REQ-BETA"}


def test_matrix_coverage_gaps_flags_blank_refs():
    gaps = hv.matrix_coverage_gaps(_MATRIX_8COL)
    assert gaps == {"REQ-FEAT-003": ["design_ref", "code_ref", "test_ref"]}


def test_matrix_coverage_gaps_missing_column_counts_for_every_row():
    no_code = """
| req_id | design_ref | test_ref |
|---|---|---|
| REQ-FEAT-001 | D-19 | TC-001 |
"""
    assert hv.matrix_coverage_gaps(no_code) == {"REQ-FEAT-001": ["code_ref"]}


def test_parse_matrix_legacy_7col():
    header, rows = hv.parse_matrix(_MATRIX_8COL)
    assert header["req_id"] == 1 and len(rows) == 3


def test_reqs_without_task():
    tasks = "| TASK-001 | impl REQ-FEAT-001 | ... |\n| TASK-002 | impl REQ-FEAT-002 |"
    reqs = ["REQ-FEAT-001", "REQ-FEAT-002", "REQ-FEAT-040"]
    assert hv.reqs_without_task(reqs, tasks) == ["REQ-FEAT-040"]


# --- T2.11 anti-churn ---

_REV_HISTORY = """
| Version | Date | By | Notes |
|---|---|---|---|
| 1.0 | 2026-01-01 | x | init |
| 1.1 | 2026-01-02 | x | edit |
| 2.0 | 2026-01-03 | x | rewrite |
"""


def test_revision_count_counts_dated_rows():
    assert hv.revision_count(_REV_HISTORY) == 3


def test_revision_count_ignores_non_dated_version_table():
    # a table whose first cell is N.N but second cell is NOT a date is not a revision row
    not_rev = "| 1.0 | high | scope |\n| 2.0 | low | other |"
    assert hv.revision_count(not_rev) == 0


def test_churn_assessment_flags_high_churn():
    a = hv.churn_assessment(_REV_HISTORY, threshold=2)
    assert a == {"revisions": 3, "threshold": 2, "high_churn": True}
    assert hv.churn_assessment(_REV_HISTORY, threshold=4)["high_churn"] is False


# --- T1.3 version-coherence ---

def test_doc_version_from_frontmatter():
    assert hv.doc_version('---\ntitle: x\nversion: "2.3"\nstatus: draft\n---\n') == "2.3"
    assert hv.doc_version("no frontmatter here") is None


def test_version_citations_binds_to_nearest_doc():
    cites = hv.version_citations("Synced D-02 (v2.2), D-19 (v2.3) today.")
    assert ("D-02", "2.2") in cites and ("D-19", "2.3") in cites


def test_version_citations_skips_revision_rows():
    # a dated revision row that mentions an old version is history, not a cross-ref
    line = "| 1.1 | 2026-06-18 | x | synced to D-02 v1.6 |"
    assert hv.version_citations(line) == []


def test_version_coherence_flags_stale_citation():
    issues = hv.version_coherence(
        {"D-02": "2.3"}, {"D-26": "Per D-02 (v2.2) the scope is..."}
    )
    assert issues == [{"source": "D-26", "doc": "D-02", "cited": "2.2", "declared": "2.3"}]


def test_version_coherence_clean_when_aligned():
    assert hv.version_coherence({"D-02": "2.3"}, {"D-26": "Per D-02 v2.3 ..."}) == []


# --- T1.2 spec-ref lint ---

def test_spec_ref_leaks_finds_all_id_kinds():
    code = "# REQ-FEAT-001\nassert x == y  # TC-005\nraise Error('NFR-002')\nok = 1"
    leaks = hv.spec_ref_leaks(code)
    assert set(leaks) == {"REQ-FEAT-001", "TC-005", "NFR-002"}


def test_spec_ref_leaks_clean_code():
    assert hv.spec_ref_leaks("def f():\n    return 42\n") == []


# --- T1.1 MODEL_DRIFT ---

_D19 = """
### 3.1 Resource Plan
- **Tên vật lý (Physical name)**: `resource_plan`
### 3.2 Resource Plan Request
- **Tên vật lý (Physical name)**: `resource.plan.request`
- Theo mẫu `project.invoice.member.summary` (external).
Naming: tên vật lý theo `snake_case` kiểu Odoo.
"""


def test_model_tokens_only_declaration_subjects():
    toks = hv.model_tokens_from_design(_D19)
    assert toks == {"resource_plan", "resource.plan.request"}  # not snake_case, not the "theo mẫu" ref


def test_model_drift_design_only():
    code = "class X(models.Model):\n    _name = 'resource.plan'\n"
    d = hv.model_drift(_D19, code)
    assert d["design_only"] == ["resource.plan.request"]  # request model absent from code
    assert d["code_only"] == [] and d["drift"] is True


def test_model_drift_underscore_dotted_tolerant():
    # design declares underscore table name; code declares the dotted _name → no drift
    design = "- **Physical name**: `resource_plan_summary`"
    code = "_name = 'resource.plan.summary'"
    assert hv.model_drift(design, code)["design_only"] == []


def test_model_drift_code_only_rogue_model():
    design = "- **Physical name**: `resource.plan`"
    code = "_name = 'resource.plan'\n_name = 'rogue.model'"
    assert hv.model_drift(design, code)["code_only"] == ["rogue.model"]


# --- T2.12 semantic-review status ---

def test_semantic_review_passed_when_facets_empty():
    fm = 'semanticReview:\n  status: passed\n  openFacets: []\n'
    s = hv.semantic_review_status(fm)
    assert s == {"status": "passed", "open_facets_empty": True, "passed": True}


def test_semantic_review_not_passed_when_facets_present_inline():
    fm = 'semanticReview:\n  status: passed\n  openFacets: ["REQ-013 admin facet"]\n'
    assert hv.semantic_review_status(fm)["passed"] is False


def test_semantic_review_not_passed_when_facets_present_block():
    fm = "semanticReview:\n  status: passed\n  openFacets:\n    - REQ-013 admin facet\n"
    s = hv.semantic_review_status(fm)
    assert s["open_facets_empty"] is False and s["passed"] is False


def test_semantic_review_pending_status():
    fm = "semanticReview:\n  status: pending\n  openFacets: []\n"
    assert hv.semantic_review_status(fm)["passed"] is False


def test_semantic_review_missing_block():
    assert hv.semantic_review_status("---\ntitle: x\n---")["passed"] is False


# --- F-3 review regressions (U1) ---

def test_model_drift_longer_name_does_not_mask_shorter():
    # F-3 #1: dotted substring must not mask — design has old `resource.plan`,
    # code only the new `resource.plan.request` → the old model IS drift.
    design = "- **Physical name**: `resource.plan`"
    code = "_name = 'resource.plan.request'"
    assert hv.model_drift(design, code)["design_only"] == ["resource.plan"]


def test_model_drift_multiline_name_detected():
    # F-3 #4: a _name wrapped onto the next line is still a real code model.
    design = "- **Physical name**: `resource.plan.request`"
    code = "_name = (\n    'resource.plan.request'\n)"
    assert hv.model_drift(design, code)["design_only"] == []


def test_semantic_review_quoted_status():
    # F-3 #2: quoted status must still read as passed.
    fm = 'semanticReview:\n  status: "passed"\n  openFacets: []\n'
    assert hv.semantic_review_status(fm)["passed"] is True


def test_semantic_review_absent_facets_key_not_pass():
    # F-3 #4: omitting openFacets must NOT earn a pass.
    fm = "semanticReview:\n  status: passed\n"
    s = hv.semantic_review_status(fm)
    assert s["open_facets_empty"] is None and s["passed"] is False


def test_semantic_review_blankline_in_facet_list_not_pass():
    # F-3 #1 (edge): a blank line before the list must not hide the open facet.
    fm = "semanticReview:\n  status: passed\n  openFacets:\n\n    - read\n"
    assert hv.semantic_review_status(fm)["passed"] is False


def test_parse_matrix_spaced_header_variant():
    # F-3 #2 (adv): `req id` / `design ref` headers must still parse.
    matrix = (
        "| req id | design ref | code ref | test ref |\n"
        "|---|---|---|---|\n"
        "| REQ-FEAT-001 |  |  |  |\n"
    )
    gaps = hv.matrix_coverage_gaps(matrix)
    assert gaps == {"REQ-FEAT-001": ["design_ref", "code_ref", "test_ref"]}


def test_version_token_three_part_not_truncated():
    assert ("D-02", "2.2.1") in hv.version_citations("Per D-02 v2.2.1 ...")


def test_primitives_tolerate_none():
    assert hv.revision_count(None) == 0
    assert hv.doc_version(None) is None
    assert hv.spec_ref_leaks(None) == []
    assert hv.missing_from_matrix(None, None) == []
    assert hv.model_drift(None, None)["drift"] is False
    assert hv.semantic_review_status(None)["passed"] is False
    assert hv.matrix_coverage_gaps(None) == {}


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
