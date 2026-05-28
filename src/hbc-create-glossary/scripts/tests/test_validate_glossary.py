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
title: "Test 用語集"
version: "1.0"
status: complete
lastStep: complete
---

# Test 用語集 (Glossary)

## 用語一覧 (Terms)

| 用語 (Term) | 意味 (Definition) | カテゴリ (Category) |
|-------------|-------------------|---------------------|
| オーダー | 顧客からの注文。商品と数量を含む | ビジネス |
| ステータス | オーダーの現在の状態（pending, confirmed, shipped） | ビジネス |
| バリデーション | 入力データの整合性チェック | テクニカル |

## 略語一覧 (Abbreviations)

| 略語 (Abbreviation) | 正式名称 (Full Name) | 意味 (Definition) |
|---------------------|---------------------|-------------------|
| OMS | Order Management System | 注文管理システム |
| SKU | Stock Keeping Unit | 在庫管理単位 |

## 改訂履歴 (Revision History)

| バージョン (Version) | 日付 (Date) | 担当者 (Author) | 改訂内容 (Scope of Change) |
|---------------------|-------------|-----------------|---------------------------|
| 1.0 | 2026-05-27 | Test | 初版作成 |
"""


def run_script(doc_content: str, extra_args: list[str] | None = None) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-03-test.md"
        doc_path.write_text(doc_content, encoding="utf-8")

        cmd = [sys.executable, SCRIPT, str(doc_path), "--project-root", tmpdir]
        if extra_args:
            cmd.extend(extra_args)

        result = subprocess.run(cmd, capture_output=True, text=True)
        output = json.loads(result.stdout)
        return output, result.returncode


def test_valid_document():
    result, code = run_script(VALID_DOC)
    assert code == 0, f"Expected exit 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["term_count"] == 3
    assert result["abbreviation_count"] == 2
    assert result["total_entries"] == 5


def test_duplicate_terms():
    doc = VALID_DOC.replace(
        "| バリデーション | 入力データの整合性チェック | テクニカル |",
        "| オーダー | 別の定義 | テクニカル |"
    )
    result, code = run_script(doc)
    assert code == 1
    dup = [i for i in result["issues"] if i["type"] == "DUPLICATE_TERM"]
    assert len(dup) > 0
    assert dup[0]["auto_fixable"] is True


def test_empty_definition():
    doc = VALID_DOC.replace(
        "| ステータス | オーダーの現在の状態（pending, confirmed, shipped） | ビジネス |",
        "| ステータス | | ビジネス |"
    )
    result, code = run_script(doc)
    empty = [i for i in result["issues"] if i["type"] == "EMPTY_DEFINITION"]
    assert len(empty) > 0
    assert empty[0]["term"] == "ステータス"


def test_no_terms():
    doc = """\
---
document_id: D-03
---

# Test 用語集

## 用語一覧 (Terms)

| 用語 (Term) | 意味 (Definition) | カテゴリ (Category) |
|-------------|-------------------|---------------------|

## 略語一覧 (Abbreviations)

| 略語 (Abbreviation) | 正式名称 (Full Name) | 意味 (Definition) |
|---------------------|---------------------|-------------------|

## 改訂履歴 (Revision History)

| Version | Date | Author | Scope |
|---------|------|--------|-------|
"""
    result, code = run_script(doc)
    no_terms = [i for i in result["issues"] if i["type"] == "NO_TERMS"]
    assert len(no_terms) > 0


def test_missing_section():
    doc = VALID_DOC.replace("## 略語一覧 (Abbreviations)", "## Removed Section")
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    sections = {i["section"] for i in missing}
    assert "略語一覧" in sections


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/file.md", "--project-root", "/tmp"]
    result = subprocess.run(cmd, capture_output=True, text=True)
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
        subprocess.run(cmd, capture_output=True, text=True)

        assert out_path.exists()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert "valid" in data


def test_cross_table_duplicate():
    doc = VALID_DOC.replace(
        "| OMS | Order Management System | 注文管理システム |",
        "| オーダー | Order | 注文 |"
    )
    result, _ = run_script(doc)
    dup = [i for i in result["issues"] if i["type"] == "DUPLICATE_TERM"]
    assert len(dup) > 0


if __name__ == "__main__":
    tests = [
        test_valid_document,
        test_duplicate_terms,
        test_empty_definition,
        test_no_terms,
        test_missing_section,
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
