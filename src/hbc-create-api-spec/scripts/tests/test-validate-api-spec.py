#!/usr/bin/env python3
"""Tests for validate-api-spec.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

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
        import subprocess

        path = str(tmp_path / "d21.md")
        _write(path, MINIMAL_VALID)

        script = os.path.join(
            os.path.dirname(__file__), "..", "validate-api-spec.py"
        )
        result = subprocess.run(
            [sys.executable, script, path],
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
