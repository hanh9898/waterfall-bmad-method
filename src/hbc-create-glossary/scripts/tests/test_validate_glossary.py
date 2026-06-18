#!/usr/bin/env python3
"""Tests for validate-glossary.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-glossary.py")

VALID_DOC = """\
---
document_id: D-03
title: "Test Bảng từ vựng"
version: "1.0"
status: complete
lastStep: complete
---

# Test D-03 Bảng từ vựng

## Thuật ngữ

| Thuật ngữ | Định nghĩa | Phân loại |
|-----------|------------|-----------|
| Đơn hàng | Yêu cầu mua từ khách, gồm sản phẩm và số lượng | Nghiệp vụ |
| Trạng thái | Tình trạng hiện tại của đơn (pending, confirmed, shipped) | Nghiệp vụ |
| Kiểm tra hợp lệ | Kiểm tra tính toàn vẹn dữ liệu đầu vào | Kỹ thuật |

## Từ viết tắt

| Từ viết tắt | Tên đầy đủ | Định nghĩa |
|-------------|-----------|------------|
| OMS | Order Management System | Hệ thống quản lý đơn hàng |
| SKU | Stock Keeping Unit | Đơn vị quản lý tồn kho |

## Lịch sử sửa đổi

| Phiên bản | Ngày | Người thực hiện | Nội dung sửa đổi |
|-----------|------|-----------------|------------------|
| 1.0 | 2026-05-27 | Test | Bản đầu |
"""


def run_script(doc_content: str, extra_args: list[str] | None = None) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-03-test.md"
        doc_path.write_text(doc_content, encoding="utf-8")

        cmd = [sys.executable, SCRIPT, str(doc_path), "--project-root", tmpdir]
        if extra_args:
            cmd.extend(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        output = json.loads(result.stdout)
        return output, result.returncode


def test_valid_document():
    result, code = run_script(VALID_DOC)
    assert code == 0, f"Expected exit 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["term_count"] == 3
    assert result["abbreviation_count"] == 2
    assert result["total_entries"] == 5
    # honest verdict (S-3) fields present
    assert result["structure_ok"] is True
    assert result["semantic_review"] == "n/a"
    assert result["passed"] is True
    assert "not_checked" in result and result["not_checked"]


def test_duplicate_terms():
    doc = VALID_DOC.replace(
        "| Kiểm tra hợp lệ | Kiểm tra tính toàn vẹn dữ liệu đầu vào | Kỹ thuật |",
        "| Đơn hàng | Định nghĩa khác | Kỹ thuật |"
    )
    result, code = run_script(doc)
    assert code == 1
    dup = [i for i in result["issues"] if i["type"] == "DUPLICATE_TERM"]
    assert len(dup) > 0
    assert dup[0]["auto_fixable"] is True


def test_empty_definition():
    doc = VALID_DOC.replace(
        "| Trạng thái | Tình trạng hiện tại của đơn (pending, confirmed, shipped) | Nghiệp vụ |",
        "| Trạng thái | | Nghiệp vụ |"
    )
    result, code = run_script(doc)
    empty = [i for i in result["issues"] if i["type"] == "EMPTY_DEFINITION"]
    assert len(empty) > 0
    assert empty[0]["term"] == "Trạng thái"


def test_no_terms():
    doc = """\
---
document_id: D-03
---

# Test D-03

## Thuật ngữ

| Thuật ngữ | Định nghĩa | Phân loại |
|-----------|------------|-----------|

## Từ viết tắt

| Từ viết tắt | Tên đầy đủ | Định nghĩa |
|-------------|-----------|------------|

## Lịch sử sửa đổi

| Phiên bản | Ngày | Người thực hiện | Nội dung |
|-----------|------|-----------------|----------|
"""
    result, code = run_script(doc)
    no_terms = [i for i in result["issues"] if i["type"] == "NO_TERMS"]
    assert len(no_terms) > 0


def test_missing_section():
    doc = VALID_DOC.replace("## Từ viết tắt", "## Removed Section")
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    sections = {i["section"] for i in missing}
    assert "Abbreviations" in sections


def test_section_recognized_in_vietnamese():
    # Vietnamese headings must satisfy the section check (no Japanese needed)
    result, code = run_script(VALID_DOC)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"Vietnamese sections not recognized: {missing}"


def test_abbrev_empty_definition_flagged():
    # Bug B2: definition was hardcoded to cells[1] (the "Tên đầy đủ"/Full Form
    # column) for the Abbreviations table, whose definition is cells[2]. An empty
    # Definition (col 2) with a present Full Form (col 1) therefore passed.
    doc = VALID_DOC.replace(
        "| OMS | Order Management System | Hệ thống quản lý đơn hàng |",
        "| OMS | Order Management System | |",
    )
    result, _ = run_script(doc)
    empty = [i for i in result["issues"] if i["type"] == "EMPTY_DEFINITION"]
    assert any(i["term"] == "OMS" for i in empty)


def test_abbrev_empty_fullform_not_flagged_as_missing_definition():
    # Bug B2 (other direction): an empty Full Form (col 1) but present Definition
    # (col 2) was wrongly flagged EMPTY_DEFINITION because col 1 was read as the
    # definition. Full Form being blank is not a missing-definition defect.
    doc = VALID_DOC.replace(
        "| OMS | Order Management System | Hệ thống quản lý đơn hàng |",
        "| OMS | | Hệ thống quản lý đơn hàng |",
    )
    result, _ = run_script(doc)
    empty = [i for i in result["issues"] if i["type"] == "EMPTY_DEFINITION"]
    assert not any(i["term"] == "OMS" for i in empty)


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/file.md", "--project-root", "/tmp"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert "error" in output


def test_output_to_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-03-test.md"
        doc_path.write_text(VALID_DOC, encoding="utf-8")
        out_path = Path(tmpdir) / "result.json"

        cmd = [
            sys.executable, SCRIPT, str(doc_path),
            "--project-root", tmpdir,
            "-o", str(out_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

        assert out_path.exists()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert "valid" in data
        assert "structure_ok" in data


def test_cross_table_duplicate():
    doc = VALID_DOC.replace(
        "| OMS | Order Management System | Hệ thống quản lý đơn hàng |",
        "| Đơn hàng | Order | đơn |"
    )
    result, _ = run_script(doc)
    dup = [i for i in result["issues"] if i["type"] == "DUPLICATE_TERM"]
    assert len(dup) > 0


if __name__ == "__main__":
    tests = [
        test_valid_document,
        test_duplicate_terms,
        test_empty_definition,
        test_abbrev_empty_definition_flagged,
        test_abbrev_empty_fullform_not_flagged_as_missing_definition,
        test_no_terms,
        test_missing_section,
        test_section_recognized_in_vietnamese,
        test_missing_document,
        test_output_to_file,
        test_cross_table_duplicate,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
