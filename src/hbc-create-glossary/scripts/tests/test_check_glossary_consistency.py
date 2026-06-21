#!/usr/bin/env python3
"""Tests for check-glossary-consistency.py (B11-2 orphan / B11-3 ubiquitous-language)."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "check-glossary-consistency.py")

GLOSSARY = """\
---
document_id: D-03
---

# Glossary

## Thuật ngữ

| Thuật ngữ | Định nghĩa | Phân loại |
|-----------|------------|-----------|
| Đơn xin nguồn lực | Yêu cầu phân bổ nguồn lực (`resource.plan.request`) | Nghiệp vụ |
| Ảnh chụp kế hoạch | Bản đông cứng của kế hoạch (`resource.plan.snapshot`) tại một thời điểm | Nghiệp vụ |

## Từ viết tắt

| Từ viết tắt | Tên đầy đủ | Định nghĩa |
|-------------|-----------|------------|
| RPB | Resource Plan Billable | Mô-đun kế hoạch nguồn lực tính phí |

## Lịch sử sửa đổi

| Phiên bản | Ngày | Người thực hiện | Nội dung |
|-----------|------|-----------------|----------|
| 1.0 | 2026-06-22 | Test | Bản đầu |
"""

D19 = """\
# D-19

### Đơn xin nguồn lực
- Physical name (Tên vật lý): `resource.plan.request`

### Ảnh chụp kế hoạch
- Physical name (Tên vật lý): `resource.plan.snapshot`
"""

CODE = """\
from odoo import models, fields

class ResourcePlanRequest(models.Model):
    _name = 'resource.plan.request'

class ResourcePlanSummary(models.Model):
    _name = 'resource.plan.summary'
"""


def write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content, encoding="utf-8")
    return p


def run(args: list[str]) -> tuple[dict, int]:
    cmd = [sys.executable, SCRIPT, *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout), r.returncode


def test_clean_when_all_models_reflected():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)
        d19 = write(tmp, "D-19.md", D19)  # only request + snapshot, both reflected
        result, code = run([str(g), "--design", str(d19)])
        assert result["missing_from_glossary"] == [], result["missing_from_glossary"]
        assert result["grounded"] is True
        assert code == 0


def test_missing_from_glossary_flags_code_only_model():
    # resource.plan.summary is in CODE but reflected nowhere in the glossary → B11-3 gap
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)
        code_dir = tmp / "models"
        code_dir.mkdir()
        write(code_dir, "rpb.py", CODE)
        result, rc = run([str(g), "--code-dir", str(code_dir)])
        toks = result["missing_from_glossary"]
        assert "resource.plan.summary" in toks, toks
        assert "resource.plan.request" not in toks  # reflected in a definition
        assert rc == 1
        assert any(i["type"] == "MISSING_FROM_GLOSSARY" for i in result["issues"])


def test_design_token_absent_from_glossary_flagged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        # drop the snapshot term so its design model is unreflected
        gloss = GLOSSARY.replace(
            "| Ảnh chụp kế hoạch | Bản đông cứng của kế hoạch (`resource.plan.snapshot`) tại một thời điểm | Nghiệp vụ |\n",
            "",
        )
        g = write(tmp, "D-03.md", gloss)
        d19 = write(tmp, "D-19.md", D19)
        result, rc = run([str(g), "--design", str(d19)])
        assert "resource.plan.snapshot" in result["missing_from_glossary"]


def test_orphan_term_flagged():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)
        # source corpus mentions only one of the terms
        src = write(tmp, "D-02.md", "Hệ thống xử lý Đơn xin nguồn lực của người dùng.")
        result, rc = run([str(g), "--sources", str(src)])
        orphans = result["orphan_terms"]
        assert "Ảnh chụp kế hoạch" in orphans, orphans
        assert "Đơn xin nguồn lực" not in orphans
        assert rc == 1


def test_no_orphan_when_term_in_corpus():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)
        # corpus that names every glossary term (incl. the RPB abbreviation)
        src = write(tmp, "D-02.md",
                    "Mô-đun RPB xử lý Đơn xin nguồn lực và lưu Ảnh chụp kế hoạch.")
        result, rc = run([str(g), "--sources", str(src)])
        assert result["orphan_terms"] == [], result["orphan_terms"]
        assert rc == 0


def test_advisory_when_nothing_supplied():
    # no --design/--code-dir/--sources → nothing to reconcile, clean+grounded false
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)
        result, rc = run([str(g)])
        assert rc == 0
        assert result["grounded"] is False
        assert result["missing_from_glossary"] == []
        assert result["orphan_terms"] == []
        assert result["valid"] is True


def test_honest_verdict_fields():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)
        d19 = write(tmp, "D-19.md", D19)
        result, _ = run([str(g), "--design", str(d19)])
        assert "structure_ok" in result
        assert result["semantic_review"] == "n/a"
        assert "not_checked" in result and result["not_checked"]
        assert "term_count" in result


def test_code_under_excluded_ancestor_still_scanned():
    # Regression (CRITICAL): exclusion must be RELATIVE to --code-dir, not the
    # absolute path. A project under a 'tests'/'migrations' ANCESTOR must still have
    # its models scanned — else B11-3 silently false-greens.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)  # does not reflect 'a.b.unseen'
        models = tmp / "tests" / "proj" / "models"  # 'tests' is an ANCESTOR of code-dir
        models.mkdir(parents=True)
        write(models, "m.py", "class M(models.Model):\n    _name = 'a.b.unseen'\n")
        result, rc = run([str(g), "--code-dir", str(models)])
        assert "a.b.unseen" in result["missing_from_glossary"], result["missing_from_glossary"]
        assert rc == 1


def test_wizard_under_code_dir_still_excluded():
    # The relative-parts exclusion must still drop a wizard/ subdir UNDER code-dir.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)
        code = tmp / "code"
        (code / "wizard").mkdir(parents=True)
        write(code / "wizard", "w.py", "class W(models.TransientModel):\n    _name = 'a.b.wiz'\n")
        result, rc = run([str(g), "--code-dir", str(code)])
        assert "a.b.wiz" not in result["missing_from_glossary"]


def test_nonexistent_code_dir_is_loud_error():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)
        result, rc = run([str(g), "--code-dir", str(tmp / "does-not-exist")])
        assert rc == 2
        assert "error" in result


def test_duplicate_term_rows_reported_once():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        gloss = GLOSSARY.replace(
            "| Ảnh chụp kế hoạch | Bản đông cứng của kế hoạch (`resource.plan.snapshot`) tại một thời điểm | Nghiệp vụ |\n",
            "| Đơn xin nguồn lực | Trùng lặp | Nghiệp vụ |\n",  # duplicate of first term
        )
        g = write(tmp, "D-03.md", gloss)
        src = write(tmp, "D-02.md", "Tài liệu không nhắc tới thuật ngữ nào.")
        result, rc = run([str(g), "--sources", str(src)])
        orphans = result["orphan_terms"]
        assert orphans.count("Đơn xin nguồn lực") == 1, orphans


def test_project_root_resolves_relative_paths():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        write(tmp, "D-03.md", GLOSSARY)
        write(tmp, "D-19.md", D19)
        # pass bare (relative) paths + --project-root
        result, rc = run(["D-03.md", "--project-root", str(tmp), "--design", "D-19.md"])
        assert result["grounded"] is True
        assert "error" not in result


def test_orphan_skipped_when_only_code_supplied():
    # B11-2 must NOT flag human-language terms against a code-only corpus.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        g = write(tmp, "D-03.md", GLOSSARY)
        code = tmp / "models"
        code.mkdir()
        write(code, "rpb.py", CODE)
        result, rc = run([str(g), "--code-dir", str(code)])
        assert result["orphan_terms"] == [], result["orphan_terms"]


def test_missing_glossary_file():
    result, rc = run(["/nonexistent/D-03.md"])
    assert rc == 2
    assert "error" in result


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
