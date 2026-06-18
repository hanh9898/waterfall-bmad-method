#!/usr/bin/env python3
"""Tests for validate-requirements.py."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-requirements.py")

VALID_DOC = """\
---
document_id: D-02
title: "Test Đặc tả yêu cầu"
version: "1.0"
status: draft
---

# Test Đặc tả yêu cầu

## 1. Tổng quan dự án

### 1.1 Mục đích

System for managing orders.

### 1.2 Các bên liên quan

| Name | Role | Responsibility |
|------|------|---------------|
| Alice | PM | Project management |

### 1.3 Mốc thời gian

Deadline: 2026-06-30

## 2. Phạm vi

### 2.1 Hạng mục bao gồm

- Order management
- User authentication

### 2.2 Hạng mục loại trừ

- Payment processing

## 3. Vai trò người dùng

| Role | Description | Key Requirements |
|------|-------------|-----------------|
| Admin | System administrator | Auth, Order |

## 4. Yêu cầu chức năng

| REQ ID | Category | Requirement | Priority | User Role | Acceptance Criteria |
|--------|----------|-------------|----------|-----------|-------------------|
| REQ-001 | Auth | User can login | High | Admin | Login succeeds with valid credentials |
| REQ-002 | Order | User can create order | High | Admin | Order created with valid data |
| REQ-003 | Order | User can view orders | Medium | Admin | Order list displays all orders |

## 5. Yêu cầu phi chức năng

### 5.1 Hiệu năng

| NFR ID | Requirement | Measurable Criteria |
|--------|-------------|-------------------|
| NFR-001 | Response time | < 2 seconds for 95th percentile |

### 5.2 Bảo mật

| NFR ID | Requirement | Measurable Criteria |
|--------|-------------|-------------------|
| NFR-002 | Password hashing | bcrypt with cost factor 12 |

## 6. Ràng buộc và giả định

### 6.1 Công nghệ

PostgreSQL 15, Python 3.12

### 6.2 Giả định

Cloud hosting available
"""


def run_script(doc_content: str, extra_args: list[str] | None = None) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-02-test.md"
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
    assert result["total_issues"] == 0
    assert result["req_count"] == 3
    # honest verdict (S-3) fields present and consistent
    assert result["structure_ok"] is True
    assert result["semantic_review"] == "n/a"
    assert result["passed"] is True
    assert "not_checked" in result and result["not_checked"]


def test_prose_req_reference_not_counted_as_duplicate():
    # REQ-001 referenced in prose (User Roles cell) must NOT trip duplicate (S-4)
    doc = VALID_DOC.replace(
        "| Admin | System administrator | Auth, Order |",
        "| Admin | System administrator, see REQ-001 | Auth, Order |",
    )
    result, code = run_script(doc)
    dup = [i for i in result["issues"] if i["type"] == "REQ_ID_DUPLICATE"]
    assert dup == [], f"prose REQ reference wrongly flagged: {dup}"
    assert result["valid"] is True
    assert result["req_count"] == 3


def test_intra_table_prose_ref_not_counted():
    # F7: an id-less row whose other cell references a REQ must NOT create a ghost id
    doc = VALID_DOC.replace(
        "| REQ-003 | Order | User can view orders | Medium | Admin | Order list displays all orders |",
        "| REQ-003 | Order | User can view orders | Medium | Admin | Order list displays all orders |\n"
        "|  | Order | Sub-requirement | Low | Admin | See REQ-001 for details |",
    )
    result, code = run_script(doc)
    dup = [i for i in result["issues"] if i["type"] == "REQ_ID_DUPLICATE"]
    assert dup == [], f"prose REQ ref in a cell wrongly counted: {dup}"
    assert result["req_count"] == 3


def test_duplicate_req_ids():
    doc = VALID_DOC.replace("REQ-003", "REQ-001")
    result, code = run_script(doc)
    assert code == 1
    assert result["valid"] is False
    dup_issues = [i for i in result["issues"] if i["type"] == "REQ_ID_DUPLICATE"]
    assert len(dup_issues) > 0
    assert dup_issues[0]["auto_fixable"] is True


def test_gap_in_req_ids():
    doc = VALID_DOC.replace("REQ-002", "REQ-005")
    result, code = run_script(doc)
    gap_issues = [i for i in result["issues"] if i["type"] == "REQ_ID_GAP"]
    assert len(gap_issues) > 0
    assert "REQ-002" in gap_issues[0]["message"]


def test_vague_terms_detected():
    doc = VALID_DOC.replace(
        "User can login",
        "User can login easily with a simple interface"
    )
    result, code = run_script(doc)
    vague_issues = [i for i in result["issues"] if i["type"] == "VAGUE_TERM"]
    terms_found = {i["term"] for i in vague_issues}
    assert "easy" in terms_found or "simple" in terms_found


def test_custom_vague_terms():
    result, code = run_script(VALID_DOC, ["--vague-terms", "order,login"])
    vague_issues = [i for i in result["issues"] if i["type"] == "VAGUE_TERM"]
    assert len(vague_issues) > 0


def test_missing_section():
    doc = VALID_DOC.replace("## 2. Phạm vi", "## 2. Removed")
    result, code = run_script(doc)
    missing_issues = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    sections = {i["section"] for i in missing_issues}
    assert "Scope" in sections


def test_empty_section():
    doc = VALID_DOC.replace(
        "| Admin | System administrator | Auth, Order |",
        "",
    )
    result, _ = run_script(doc)
    empty_issues = [i for i in result["issues"] if i["type"] == "SECTION_EMPTY"]
    assert len(empty_issues) > 0
    sections = {i["section"] for i in empty_issues}
    assert "User Roles" in sections


def test_nfr_missing_criteria():
    doc = VALID_DOC.replace(
        "| NFR-001 | Response time | < 2 seconds for 95th percentile |",
        "| NFR-001 | Response time | |"
    )
    result, _ = run_script(doc)
    nfr_issues = [i for i in result["issues"] if i["type"] == "NFR_NO_CRITERIA"]
    assert len(nfr_issues) > 0
    assert nfr_issues[0]["nfr_id"] == "NFR-001"


def test_vague_terms_skip_frontmatter_and_code_fence():
    # Bug A5: check_vague_terms scanned the whole file, so a vague word in the YAML
    # frontmatter title or inside a fenced code example produced a blocking
    # false-fail. Those regions must be skipped; only requirement text is scanned.
    doc = VALID_DOC.replace(
        'title: "Test Đặc tả yêu cầu"',
        'title: "A simple and easy system"',
    ).replace(
        "System for managing orders.",
        "System for managing orders.\n\n```python\n# an easy, simple example\nx = 1\n```",
    )
    result, code = run_script(doc)
    vague_issues = [i for i in result["issues"] if i["type"] == "VAGUE_TERM"]
    assert vague_issues == [], f"frontmatter/code-fence vague terms must be ignored: {vague_issues}"


def test_nfr_namespaced_missing_criteria():
    # Bug B1: `NFR-\\d+` skipped namespaced ids, so NFR-AUTH-001 with empty
    # criteria was never checked (false pass).
    doc = VALID_DOC.replace(
        "| NFR-001 | Response time | < 2 seconds for 95th percentile |",
        "| NFR-AUTH-001 | Response time | |",
    )
    result, _ = run_script(doc)
    nfr_issues = [i for i in result["issues"] if i["type"] == "NFR_NO_CRITERIA"]
    assert any(i["nfr_id"] == "NFR-AUTH-001" for i in nfr_issues)


def test_nfr_four_column_empty_criteria_flagged():
    # Bug B1: hardcoded 3-column regex read the wrong cell as "criteria" on a
    # 4-column NFR table, so an empty Measurable-Criteria column passed. The fix
    # reads the LAST column.
    doc = VALID_DOC.replace(
        "| NFR ID | Requirement | Measurable Criteria |\n"
        "|--------|-------------|-------------------|\n"
        "| NFR-001 | Response time | < 2 seconds for 95th percentile |",
        "| NFR ID | Category | Requirement | Measurable Criteria |\n"
        "|--------|----------|-------------|-------------------|\n"
        "| NFR-001 | Perf | Response time | |",
    )
    result, _ = run_script(doc)
    nfr_issues = [i for i in result["issues"] if i["type"] == "NFR_NO_CRITERIA"]
    assert any(i["nfr_id"] == "NFR-001" for i in nfr_issues)


def test_multisegment_feature_code_recognized():
    # Regression: a multi-segment feature code (slug resource-plan-billable →
    # REQ-RESOURCE-PLAN-BILLABLE-NNN) must be parsed; the old single-segment regex
    # read 0 REQs → false REQ_ID_MISSING.
    doc = (VALID_DOC
           .replace("REQ-001", "REQ-RESOURCE-PLAN-BILLABLE-001")
           .replace("REQ-002", "REQ-RESOURCE-PLAN-BILLABLE-002")
           .replace("REQ-003", "REQ-RESOURCE-PLAN-BILLABLE-003"))
    result, code = run_script(doc)
    assert code == 0, result
    assert result["valid"] is True
    assert result["req_count"] == 3
    assert not [i for i in result["issues"] if i["type"] == "REQ_ID_MISSING"]


_BROWNFIELD_BASE = """\
---
document_id: D-02
title: "Test"
---

# Test

## 1. Tổng quan dự án
System for orders.

## 2. Phạm vi
In scope: order. Out of scope: payment.

## 3. Vai trò người dùng
| Role | Description | Key Requirements |
|------|-------------|-----------------|
| Admin | admin | Order |

## 4. Yêu cầu chức năng

{FR}

## 5. Yêu cầu phi chức năng
| NFR ID | Requirement | Measurable Criteria |
|--------|-------------|-------------------|
| NFR-001 | Response | < 2 seconds |

## 6. Ràng buộc và giả định
PostgreSQL 15.
"""

_FR_GROUNDED = """| REQ ID | Category | Requirement | Change Type | Existing System Ref | Priority | User Role | Acceptance Criteria |
|--------|----------|-------------|-------------|---------------------|----------|-----------|-------------------|
| REQ-001 | Auth | THE SYSTEM SHALL login | NEW | | High | Admin | ok |
| REQ-002 | Order | THE SYSTEM SHALL apply discount | CHANGE | flow:order-create | High | Admin | ok |

#### Change Spec — REQ-002
- AS-IS: order created without discount
- TO-BE: order created with discount applied
- Invariants: total >= 0
- Out-of-scope: payment flow
"""

_FR_UNGROUNDED = """| REQ ID | Category | Requirement | Change Type | Existing System Ref | Priority | User Role | Acceptance Criteria |
|--------|----------|-------------|-------------|---------------------|----------|-----------|-------------------|
| REQ-001 | Auth | THE SYSTEM SHALL login | NEW | | High | Admin | ok |
| REQ-002 | Order | THE SYSTEM SHALL apply discount | CHANGE | | High | Admin | ok |
"""


def test_brownfield_ungrounded_change_flagged():
    # A CHANGE REQ with no Existing System Ref and no Change Spec must fail loudly
    # under --brownfield (the vague-ask-not-reconciled case).
    doc = _BROWNFIELD_BASE.format(FR=_FR_UNGROUNDED)
    result, code = run_script(doc, ["--brownfield"])
    types = {i["type"] for i in result["issues"]}
    assert "BROWNFIELD_NO_EXISTING_REF" in types
    assert "BROWNFIELD_NO_CHANGE_SPEC" in types
    assert result["valid"] is False
    assert code == 1


def test_brownfield_grounded_change_ok():
    doc = _BROWNFIELD_BASE.format(FR=_FR_GROUNDED)
    result, code = run_script(doc, ["--brownfield"])
    assert not [i for i in result["issues"] if i["type"].startswith("BROWNFIELD_")]
    assert result["valid"] is True
    assert code == 0


def test_greenfield_skips_brownfield_checks():
    # Without --brownfield, the grounding checks must NOT run even if the table has
    # an ungrounded CHANGE row (greenfield path stays frictionless).
    doc = _BROWNFIELD_BASE.format(FR=_FR_UNGROUNDED)
    result, code = run_script(doc)
    assert not [i for i in result["issues"] if i["type"].startswith("BROWNFIELD_")]
    assert result["valid"] is True


def test_missing_document():
    cmd = [sys.executable, SCRIPT, "/nonexistent/file.md", "--project-root", "/tmp"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert "error" in output


def test_output_to_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-02-test.md"
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


def test_no_req_ids():
    doc = VALID_DOC.replace("REQ-001", "R001").replace("REQ-002", "R002").replace("REQ-003", "R003")
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "REQ_ID_MISSING"]
    assert len(missing) > 0


if __name__ == "__main__":
    tests = [
        test_valid_document,
        test_prose_req_reference_not_counted_as_duplicate,
        test_duplicate_req_ids,
        test_gap_in_req_ids,
        test_vague_terms_detected,
        test_custom_vague_terms,
        test_vague_terms_skip_frontmatter_and_code_fence,
        test_missing_section,
        test_empty_section,
        test_nfr_missing_criteria,
        test_nfr_namespaced_missing_criteria,
        test_nfr_four_column_empty_criteria_flagged,
        test_multisegment_feature_code_recognized,
        test_brownfield_ungrounded_change_flagged,
        test_brownfield_grounded_change_ok,
        test_greenfield_skips_brownfield_checks,
        test_missing_document,
        test_output_to_file,
        test_no_req_ids,
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
