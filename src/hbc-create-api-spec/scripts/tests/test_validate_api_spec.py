#!/usr/bin/env python3
"""Tests for validate-api-spec.py (D-21).

Mixes in-process unit tests (loaded via importlib because the script name has a
dash) with subprocess CLI tests that exercise the script exactly as SKILL.md
invokes it.
"""

import json
import os
import subprocess
import sys
import tempfile
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).resolve().parent.parent / "validate-api-spec.py")

# Dash in the filename → import via importlib for the in-process unit tests.
_spec = spec_from_file_location(
    "validate_api_spec",
    os.path.join(os.path.dirname(__file__), "..", "validate-api-spec.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

validate = mod.validate
check_sections = mod.check_sections
check_endpoints = mod.check_endpoints
check_req_traceability = mod.check_req_traceability
check_entity_consistency = mod.check_entity_consistency


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def run_script(doc_content: str) -> tuple[dict, int]:
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "D-21-demo.md"
        doc_path.write_text(doc_content, encoding="utf-8")
        cmd = [sys.executable, SCRIPT, str(doc_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return json.loads(result.stdout), result.returncode


MINIMAL_VALID = """---
document_id: D-21
title: "Test API"
version: "1.0"
---

# Test API

## 1. (Overview)

REST API for Test project.

## 2. (Authentication & Authorization)

JWT-based authentication with refresh tokens.

## 3. (Common Specifications)

Content-Type: application/json. Standard envelope response format.

## 4. (Endpoint List)

| # | Method | Endpoint | Description | REQ ID |
|---|--------|----------|-------------|--------|
| 1 | GET | /api/v1/users | List users | REQ-001 |
| 2 | POST | /api/v1/users | Create user | REQ-002 |
| 3 | GET | /api/v1/users/:id | Get user detail | REQ-001 |

## 5. (Endpoint Details)

### 5.1 List Users

**Method:** `GET`
**URL:** `/api/v1/users`

## 6. (Data Models)

### 6.1 User

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | integer | Yes | User ID |
| name | string | Yes | Full name |
"""


# --- subprocess CLI tests (Vietnamese-section doc, exercises the full pipeline) ---

VALID_DOC = """\
---
document_id: D-21
feature: "demo"
version: "1.0"
status: draft
---

# Demo — API Specification

## 1. Overview
API cho feature demo.

## 2. Authentication
Bearer token (JWT).

## 3. Common Specifications
JSON request/response, UTF-8, mã lỗi chuẩn.

## 4. Endpoint List

| # | Method | Endpoint | Description | REQ |
|---|--------|----------|-------------|-----|
| 1 | GET | /orders | Lấy danh sách đơn | REQ-DEMO-001 |
| 2 | POST | /orders | Tạo đơn mới | REQ-DEMO-002 |

## 5. Endpoint Details

### GET /orders
Trả về danh sách đơn. REQ-DEMO-001.

### POST /orders
Tạo đơn. REQ-DEMO-002.

## 6. Data Models

### Order
- id: int
- state: str
"""


def test_valid_document_cli():
    result, code = run_script(VALID_DOC)
    assert code == 0, f"Expected 0, got {code}: {result}"
    assert result["valid"] is True
    assert result["semantic_review"] == "n/a"
    assert result["passed"] is True


def test_missing_section_cli():
    doc = VALID_DOC.replace("## 6. Data Models", "## 6. Removed")
    result, code = run_script(doc)
    assert code == 1
    assert any(i["type"] == "SECTION_MISSING" for i in result["issues"])


def test_invalid_method_cli():
    doc = VALID_DOC.replace("| 1 | GET | /orders", "| 1 | FETCH | /orders")
    result, code = run_script(doc)
    assert any(i["type"] == "INVALID_METHOD" for i in result["issues"])


def test_no_req_reference_cli():
    doc = VALID_DOC.replace("Lấy danh sách đơn | REQ-DEMO-001", "Lấy danh sách đơn | ")
    result, code = run_script(doc)
    assert any(i["type"] == "NO_REQ_REFERENCE" for i in result["issues"])


def test_vietnamese_sections_cli():
    doc = (VALID_DOC
           .replace("## 1. Overview", "## 1. Tổng quan")
           .replace("## 2. Authentication", "## 2. Xác thực")
           .replace("## 3. Common Specifications", "## 3. Quy cách chung")
           .replace("## 4. Endpoint List", "## 4. Danh sách endpoint")
           .replace("## 5. Endpoint Details", "## 5. Chi tiết endpoint")
           .replace("## 6. Data Models", "## 6. Mô hình dữ liệu"))
    result, code = run_script(doc)
    missing = [i for i in result["issues"] if i["type"] == "SECTION_MISSING"]
    assert missing == [], f"VI sections not recognized: {missing}"


def test_missing_document_cli():
    cmd = [sys.executable, SCRIPT, "/nonexistent/D-21.md"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 1


# --- T2.11 anti-churn: validator emits a `churn` block; advisory, never flips valid ---

def test_churn_reported_low():
    result, code = run_script(VALID_DOC)
    assert "churn" in result
    assert result["churn"]["high_churn"] is False  # no revision history → 0 revisions
    assert result["valid"] is True


def test_high_churn_flagged():
    rev = """\

## Revision History

| Version | Date | Author | Change |
|---------|------|--------|--------|
| 1.0 | 2026-06-01 | a | c |
| 1.1 | 2026-06-02 | a | c |
| 1.2 | 2026-06-03 | a | c |
| 1.3 | 2026-06-04 | a | c |
| 1.4 | 2026-06-05 | a | c |
| 1.5 | 2026-06-06 | a | c |
"""
    result, code = run_script(VALID_DOC + rev)
    assert result["churn"]["revisions"] >= 5
    assert result["churn"]["high_churn"] is True
    # Advisory: high churn must NOT fail the structural verdict.
    assert result["valid"] is True
    assert code == 0


# --- in-process unit tests ---

class TestCheckSections:
    def test_all_sections_present(self):
        issues = check_sections(MINIMAL_VALID)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 0

    def test_missing_section(self):
        content = MINIMAL_VALID.replace(
            "## 2. (Authentication & Authorization)\n\nJWT-based authentication with refresh tokens.\n",
            "",
        )
        issues = check_sections(content)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 1
        assert missing[0]["section"] == "Authentication"

    def test_empty_section(self):
        content = MINIMAL_VALID.replace(
            "JWT-based authentication with refresh tokens.",
            "<!-- placeholder -->",
        )
        issues = check_sections(content)
        empty = [i for i in issues if i["type"] == "SECTION_EMPTY"]
        assert len(empty) == 1


class TestCheckEndpoints:
    def test_valid_endpoints(self):
        issues = check_endpoints(MINIMAL_VALID)
        assert len(issues) == 0

    def test_no_endpoints(self):
        content = "# API\n\n## Endpoint List\n\nNothing here."
        issues = check_endpoints(content)
        no_ep = [i for i in issues if i["type"] == "NO_ENDPOINTS"]
        assert len(no_ep) == 1

    def test_duplicate_endpoint(self):
        content = """## Endpoint List

| # | Method | Endpoint | Description | REQ ID |
|---|--------|----------|-------------|--------|
| 1 | GET | /api/v1/users | List users | REQ-001 |
| 2 | GET | /api/v1/users | List users again | REQ-002 |
"""
        issues = check_endpoints(content)
        dups = [i for i in issues if i["type"] == "DUPLICATE_ENDPOINT"]
        assert len(dups) == 1

    def test_no_req_reference(self):
        content = """## Endpoint List

| # | Method | Endpoint | Description | REQ ID |
|---|--------|----------|-------------|--------|
| 1 | GET | /api/v1/users | List users |  |
"""
        issues = check_endpoints(content)
        no_ref = [i for i in issues if i["type"] == "NO_REQ_REFERENCE"]
        assert len(no_ref) == 1

    def test_endpoint_no_number_col_no_trailing_pipe(self):
        # Bug D2: the rigid regex required a leading numeric `#` column AND a
        # trailing pipe; a header-keyed parse handles a table that omits both.
        content = """## Endpoint List

| Method | Endpoint | Description | REQ ID |
|--------|----------|-------------|--------|
| GET | /api/v1/users | List users | REQ-001
"""
        issues = check_endpoints(content)
        assert issues == []


class TestReqTraceability:
    def test_valid_refs(self, tmp_path):
        d02 = str(tmp_path / "D-02.md")
        _write(d02, "# Requirements\n\nREQ-001 Create user\nREQ-002 List users\n")
        issues = check_req_traceability(MINIMAL_VALID, d02)
        assert len(issues) == 0

    def test_orphan_req(self, tmp_path):
        d02 = str(tmp_path / "D-02.md")
        _write(d02, "# Requirements\n\nREQ-001 Create user\n")
        issues = check_req_traceability(MINIMAL_VALID, d02)
        orphans = [i for i in issues if i["type"] == "ORPHAN_REQ"]
        assert len(orphans) == 1
        assert orphans[0]["req_id"] == "REQ-002"

    def test_no_d02_no_issues(self):
        issues = check_req_traceability(MINIMAL_VALID, None)
        assert len(issues) == 0


class TestEntityConsistency:
    def test_matching_entities(self, tmp_path):
        d19 = str(tmp_path / "D-19.md")
        _write(d19, """# DB Design\n\n```mermaid\nerDiagram\n    User {\n        int id\n        string name\n    }\n```\n""")
        issues = check_entity_consistency(MINIMAL_VALID, d19)
        assert len(issues) == 0

    def test_no_d19_no_issues(self):
        issues = check_entity_consistency(MINIMAL_VALID, None)
        assert len(issues) == 0

    def test_no_er_diagram_no_issues(self, tmp_path):
        d19 = str(tmp_path / "D-19.md")
        _write(d19, "# DB Design\n\nNo diagram here.")
        issues = check_entity_consistency(MINIMAL_VALID, d19)
        assert len(issues) == 0

    def test_separator_insensitive_entity_match(self, tmp_path):
        # Bug D1: model `OrderItem` (D-21) vs entity `ORDER_ITEM` (D-19) was a
        # false ENTITY_MISMATCH — bare substring match ignored case/underscores.
        d19 = str(tmp_path / "D-19.md")
        _write(d19, "# DB\n\n```mermaid\nerDiagram\n    ORDER_ITEM {\n        int id PK\n    }\n```\n")
        d21 = "## 6. Data Models\n\n### 6.1 OrderItem\n\n| Field | Type |\n|---|---|\n"
        issues = check_entity_consistency(d21, d19)
        assert [i for i in issues if i["type"] == "ENTITY_MISMATCH"] == []

    def test_unnumbered_model_heading_matched(self, tmp_path):
        # Bug D3: `### Order` (no N.N numbering) was silently skipped → a real
        # mismatch went unreported. Now any ###-level heading names a model.
        d19 = str(tmp_path / "D-19.md")
        _write(d19, "# DB\n\n```mermaid\nerDiagram\n    ORDER {\n        int id PK\n    }\n```\n")
        ok = "## Data Models\n\n### Order\n\n| Field | Type |\n|---|---|\n"
        assert [i for i in check_entity_consistency(ok, d19) if i["type"] == "ENTITY_MISMATCH"] == []
        bad = "## Data Models\n\n### Ghost\n\n| Field | Type |\n|---|---|\n"
        assert [i for i in check_entity_consistency(bad, d19) if i["type"] == "ENTITY_MISMATCH"]


class TestFullValidation:
    def test_valid_document(self, tmp_path):
        path = str(tmp_path / "d21.md")
        _write(path, MINIMAL_VALID)
        result = validate(path)
        assert result["valid"] is True
        assert result["endpoint_count"] == 3

    def test_invalid_document(self, tmp_path):
        path = str(tmp_path / "d21.md")
        _write(path, "# Empty API spec\n\nNothing here.")
        result = validate(path)
        assert result["valid"] is False
        assert result["total_issues"] > 0

    def test_cli_exit_code(self, tmp_path):
        path = str(tmp_path / "d21.md")
        _write(path, MINIMAL_VALID)
        result = subprocess.run(
            [sys.executable, SCRIPT, path],
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True


def test_namespaced_req_traceability(tmp_path):
    # v2 regression: namespaced REQ-<FEAT>-NNN must be matched and reported with
    # the FULL id. A digits-only `REQ-(\d{3,})` skipped them → false-clean.
    d21 = "## Endpoint list\n\n| 1 | GET | /x | get | REQ-AUTH-001 |\n"
    d02 = str(tmp_path / "D-02.md")
    _write(d02, "# Requirements\n\nREQ-AUTH-001 Login\n")
    assert [i for i in check_req_traceability(d21, d02) if i["type"] == "ORPHAN_REQ"] == []
    _write(d02, "# Requirements\n\nREQ-AUTH-002 Other\n")
    orphans = [i for i in check_req_traceability(d21, d02) if i["type"] == "ORPHAN_REQ"]
    assert len(orphans) == 1 and orphans[0]["req_id"] == "REQ-AUTH-001"
