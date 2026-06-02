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

def test_parse_table_stops_before_second_table():
    doc = """\
## Yêu cầu chức năng

| REQ ID | Cat |
|--------|-----|
| REQ-001 | A |

| REQ ID | Cat |
|--------|-----|
| REQ-002 | B |
"""
    rows = hv.parse_table(doc, "Yêu cầu chức năng")
    # only the first contiguous table block — no bleed of the 2nd table's header
    assert rows == [["REQ-001", "A"]]


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


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
