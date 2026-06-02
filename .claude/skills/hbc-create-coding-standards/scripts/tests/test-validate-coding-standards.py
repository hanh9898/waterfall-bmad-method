#!/usr/bin/env python3
"""Tests for validate-coding-standards.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from importlib.util import module_from_spec, spec_from_file_location

_spec = spec_from_file_location(
    "validate_coding_standards",
    os.path.join(os.path.dirname(__file__), "..", "validate-coding-standards.py"),
)
mod = module_from_spec(_spec)
_spec.loader.exec_module(mod)

validate = mod.validate
check_sections = mod.check_sections
check_contradictions = mod.check_contradictions
check_framework_conventions = mod.check_framework_conventions
check_code_examples = mod.check_code_examples


def _write(path: str, content: str = "") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


MINIMAL_VALID = """---
document_id: D-12
title: "Test コーディング規約"
version: "1.0"
framework: "django"
---

# Test コーディング規約

## 1. 概要 (Overview)

This document defines coding standards for the Test project.

## 2. 命名規約 (Naming Conventions)

Variables use snake_case. Classes use PascalCase.

## 3. フォーマット (Formatting)

Use 4 spaces for indentation. Max line length: 120.

## 4. コメント (Comments)

Comments in English. Use docstrings for all public functions.

## 5. インポート・モジュール (Imports & Modules)

Follow isort ordering: stdlib, third-party, local.

## 6. エラーハンドリング (Error Handling)

Fail fast. Never silently swallow exceptions.

## 7. セキュリティ (Security)

Never hardcode secrets. Use environment variables.

## 8. テスト (Testing)

Use pytest. Minimum 80% coverage.

## 9. フレームワーク固有 (Framework-Specific)

Django: Follow PEP 8. Use class-based views for complex logic. Model field ordering: keys, required, optional.

## 10. Git規約 (Git Conventions)

Conventional commits: feat, fix, refactor, docs, test.

```python
# Example: naming convention
def calculate_total_price(items: list[dict]) -> float:
    return sum(item["price"] for item in items)
```

```python
# Example: error handling
try:
    result = process_data(payload)
except ValidationError as e:
    logger.error("Validation failed: %s", e)
    raise
```

```python
# Example: formatting
class OrderService:
    def __init__(self, repository: OrderRepository) -> None:
        self.repository = repository
```
"""


class TestCheckSections:
    def test_all_sections_present(self, tmp_path):
        path = str(tmp_path / "d12.md")
        _write(path, MINIMAL_VALID)
        issues = check_sections(MINIMAL_VALID)
        section_issues = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(section_issues) == 0

    def test_missing_section(self, tmp_path):
        content = MINIMAL_VALID.replace(
            "## 7. セキュリティ (Security)\n\nNever hardcode secrets. Use environment variables.\n",
            "",
        )
        issues = check_sections(content)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 1
        assert missing[0]["section"] == "Security"

    def test_empty_section(self, tmp_path):
        content = MINIMAL_VALID.replace(
            "Never hardcode secrets. Use environment variables.",
            "<!-- placeholder -->",
        )
        issues = check_sections(content)
        empty = [i for i in issues if i["type"] == "SECTION_EMPTY"]
        assert len(empty) == 1
        assert empty[0]["section"] == "Security"

    def test_english_section_names_work(self):
        content = """
## Overview

Some overview content here.

## Naming Conventions

Use snake_case.

## Formatting

Use 4 spaces.

## Comments

Write in English.

## Imports

Follow isort.

## Error Handling

Fail fast.

## Security

No secrets in code.

## Testing

Use pytest.

## Framework-Specific

Django patterns.

## Git Conventions

Conventional commits.
"""
        issues = check_sections(content)
        missing = [i for i in issues if i["type"] == "SECTION_MISSING"]
        assert len(missing) == 0


class TestCheckContradictions:
    def test_no_contradiction(self):
        content = "Use 4 spaces for indentation. Keep lines under 120 characters."
        issues = check_contradictions(content)
        assert len(issues) == 0

    def test_tab_space_contradiction(self):
        content = "Use tabs for indentation in section A.\nUse 2 spaces for indentation in section B."
        issues = check_contradictions(content)
        contradictions = [i for i in issues if i["type"] == "CONTRADICTION"]
        assert len(contradictions) == 1
        assert contradictions[0]["topic"] == "indentation"

    def test_quote_style_contradiction(self):
        content = "Always use single quotes for strings.\nPrefer double quotes for JSX attributes."
        issues = check_contradictions(content)
        contradictions = [i for i in issues if i["type"] == "CONTRADICTION"]
        assert len(contradictions) == 1
        assert contradictions[0]["topic"] == "quote style"


class TestCheckFrameworkConventions:
    def test_no_framework_no_issues(self):
        issues = check_framework_conventions("any content", None)
        assert len(issues) == 0

    def test_unknown_framework_no_issues(self):
        issues = check_framework_conventions("any content", "unknown_fw")
        assert len(issues) == 0

    def test_django_sufficient_coverage(self):
        content = "Follow PEP 8 conventions. Use class-based views. Define django models properly."
        issues = check_framework_conventions(content, "django")
        assert len(issues) == 0

    def test_django_insufficient_coverage(self):
        content = "This is a generic coding standard with no framework terms."
        issues = check_framework_conventions(content, "django")
        fw_issues = [i for i in issues if i["type"] == "FRAMEWORK_COVERAGE"]
        assert len(fw_issues) == 1
        assert fw_issues[0]["framework"] == "django"

    def test_odoo_coverage(self):
        content = "Use @api.model decorators. Follow _inherit patterns. Define ir.model access."
        issues = check_framework_conventions(content, "odoo")
        assert len(issues) == 0


class TestCheckCodeExamples:
    def test_sufficient_examples(self):
        content = """
```python
x = 1
```

```python
y = 2
```

```python
z = 3
```
"""
        issues = check_code_examples(content)
        assert len(issues) == 0

    def test_insufficient_examples(self):
        content = """
```python
x = 1
```
"""
        issues = check_code_examples(content)
        few = [i for i in issues if i["type"] == "FEW_EXAMPLES"]
        assert len(few) == 1
        assert few[0]["count"] == 1


class TestFullValidation:
    def test_valid_document(self, tmp_path):
        path = str(tmp_path / "d12.md")
        _write(path, MINIMAL_VALID)
        result = validate(path, "django")
        assert result["valid"] is True
        assert result["total_issues"] == 0
        assert result["section_count"] >= 10

    def test_invalid_document_missing_sections(self, tmp_path):
        content = "# Empty coding standards\n\nNothing here."
        path = str(tmp_path / "d12.md")
        _write(path, content)
        result = validate(path)
        assert result["valid"] is False
        assert result["total_issues"] > 0

    def test_cli_exit_code(self, tmp_path):
        import subprocess

        path = str(tmp_path / "d12.md")
        _write(path, MINIMAL_VALID)

        script = os.path.join(
            os.path.dirname(__file__), "..", "validate-coding-standards.py"
        )
        result = subprocess.run(
            [sys.executable, script, path, "--framework", "django"],
            capture_output=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True

    def test_cli_missing_file(self, tmp_path):
        import subprocess

        script = os.path.join(
            os.path.dirname(__file__), "..", "validate-coding-standards.py"
        )
        result = subprocess.run(
            [sys.executable, script, str(tmp_path / "nonexistent.md")],
            capture_output=True,
        )
        assert result.returncode == 1
